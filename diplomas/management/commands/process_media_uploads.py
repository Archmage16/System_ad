from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from diplomas.models import Upload
from diplomas.generator import generate_diplomas


class Command(BaseCommand):
    help = "Автоматическая генерация дипломов из файлов .xlsx"

    def handle(self, *args, **kwargs):
        uploads_dir = Path(settings.MEDIA_ROOT) / "uploads"
        processed_dir = uploads_dir / "processed"

        # Создаём папки, если их нет
        uploads_dir.mkdir(exist_ok=True)
        processed_dir.mkdir(exist_ok=True)

        files = list(uploads_dir.glob("*.xlsx"))
        if not files:
            self.stdout.write("Файлов для обработки не найдено.")
            return

        self.stdout.write(f"Найдено файлов для обработки: {len(files)}")

        for file_path in files:
            self.stdout.write(f"\nОбработка файла: {file_path.name}")
            relative_file_path = f"uploads/{file_path.name}"

            # Получаем все существующие записи с этим файлом
            existing_uploads = Upload.objects.filter(file=relative_file_path)
            if existing_uploads.exists():
                upload = existing_uploads.first()
                upload.status = "pending"  # сбрасываем статус для повторной генерации
                upload.save()
                self.stdout.write(f"Файл уже есть в базе (id={upload.id}), статус сброшен на pending")
            else:
                upload = Upload.objects.create(
                    file=relative_file_path,
                    status="pending"
                )
                self.stdout.write(f"Создан Upload с id={upload.id}, статус pending")

            # Генерация дипломов через generator.py
            try:
                generate_diplomas(upload)
                self.stdout.write(f"Дипломы успешно сгенерированы для Upload id={upload.id}")
            except Exception as e:
                self.stderr.write(f"Ошибка при генерации дипломов для {file_path.name}: {e}")
                upload.status = "error"
                upload.save()
                continue

            # Перемещаем исходный файл в папку processed
            target_path = processed_dir / file_path.name
            try:
                file_path.rename(target_path)
                self.stdout.write(f"Файл перемещён в processed: {target_path.name}")
            except Exception as e:
                self.stderr.write(f"Не удалось переместить файл {file_path.name}: {e}")

        total = Upload.objects.count()
        self.stdout.write(f"\nОбработка завершена. Всего записей в базе: {total}")