import io
import json
import pyexcel

from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile

from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.lib.pagesizes import A4

from PyPDF2 import PdfReader, PdfWriter

from .models import Diploma


BASE_DIR = Path(settings.BASE_DIR)
FONTS_DIR = BASE_DIR / "assets/fonts"
TEMPLATES_DIR = BASE_DIR / "assets/pdf_templates"

# ==============================
# 1. ШРИФТЫ
# ==============================

def register_fonts():
    registerFont(TTFont('KZ-TimesNewRoman', str(BASE_DIR / 'assests/fonts/KZ-TimesNewRoman.ttf')))
    registerFont(TTFont('DeutschGothic', str(BASE_DIR / 'assests/fonts/DeutschGothic.ttf')))
    registerFont(TTFont('CyrillicGoth', str(BASE_DIR / 'assests/fonts/CyrillicGoth.ttf')))
    registerFont(TTFont('Baskerville', str(BASE_DIR / 'assests/fonts/Baskerville10Pro.ttf')))


# ==============================
# 2. ПАРСИНГ ФАЙЛА
# ==============================

def parse_students(file_path):

    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    if file_path.endswith(".xls") or file_path.endswith(".xlsx"):
        arr = pyexcel.get_array(file_name=file_path)
        headers = arr[0]
        students = []

        for row in arr[1:]:
            student = dict(zip(headers, row))
            students.append(student)

        return students

    return []


# ==============================
# 3. ОБРАБОТКА ОЦЕНОК
# ==============================

def grade_to_text_ru(value):
    value = int(value)

    if value >= 90:
        return "отлично"
    if value >= 75:
        return "хорошо"
    if value >= 60:
        return "удовлетворительно"
    return "неудовлетворительно"


def grade_to_text_en(value):
    value = int(value)

    if value >= 90:
        return "excellent"
    if value >= 75:
        return "good"
    if value >= 60:
        return "satisfactory"
    return "unsatisfactory"


# ==============================
# 4. СОЗДАНИЕ СЛОЯ
# ==============================

def build_overlay(student, language="ru"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("KZ-TimesNewRoman", 16)

    full_name = student.get("ФИО") or student.get("Full Name")
    c.drawCentredString(300, 700, full_name)

    c.setFont("KZ-TimesNewRoman", 12)

    y = 650

    for key, value in student.items():
        if key in ["ФИО", "Full Name"]:
            continue

        if isinstance(value, (int, float)):
            if language == "ru":
                value = grade_to_text_ru(value)
            else:
                value = grade_to_text_en(value)

        c.drawString(80, y, f"{key}: {value}")
        y -= 20

    c.save()
    buffer.seek(0)
    return buffer


# ==============================
# 5. НАЛОЖЕНИЕ НА ШАБЛОН
# ==============================

def merge_with_template(template_path, overlay_buffer):

    template_pdf = PdfReader(open(template_path, "rb"))
    overlay_pdf = PdfReader(overlay_buffer)

    writer = PdfWriter()

    base_page = template_pdf.pages[0]
    base_page.merge_page(overlay_pdf.pages[0])

    writer.add_page(base_page)

    output_stream = io.BytesIO()
    writer.write(output_stream)

    return output_stream.getvalue()


# ==============================
# 6. ГЕНЕРАЦИЯ ДИПЛОМОВ
# ==============================

def generate_diplomas(upload):

    register_fonts()

    students = parse_students(upload.file.path)

    template_ru = BASE_DIR / "MKA/template_diploma_ru.pdf"
    template_en = BASE_DIR / "MKA/template_diploma_en.pdf"

    for student in students:

        overlay_ru = build_overlay(student, language="ru")
        overlay_en = build_overlay(student, language="en")

        diploma_ru_bytes = merge_with_template(template_ru, overlay_ru)
        diploma_en_bytes = merge_with_template(template_en, overlay_en)

        diploma = Diploma.objects.create(
            upload=upload,
            student_name=student.get("ФИО") or student.get("Full Name")
        )

        diploma.pdf_ru.save(
            f"{diploma.student_name}_RU.pdf",
            ContentFile(diploma_ru_bytes),
            save=False
        )

        diploma.pdf_en.save(
            f"{diploma.student_name}_EN.pdf",
            ContentFile(diploma_en_bytes),
            save=True
        )