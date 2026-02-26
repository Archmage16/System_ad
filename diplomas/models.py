from django.db import models


class Upload(models.Model):
    file = models.FileField(upload_to="uploads/")
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Upload {self.id} - {self.status}"


class Diploma(models.Model):
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, related_name="diplomas")
    student_name = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to="diplomas/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.student_name