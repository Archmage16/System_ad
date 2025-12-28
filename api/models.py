from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Office(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Room(models.Model):
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=50)
    max_places = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.office.name} - {self.room_number}"
    
class Computer(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="computers")
    hostname = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_fullname = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.hostname


class Incident(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    computer = models.ForeignKey(Computer, null=True, blank=True,
                                 on_delete=models.SET_NULL)
    room = models.ForeignKey(Room, null=True, blank=True,
                             on_delete=models.SET_NULL)

    user_message = models.TextField()
    photo_url = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Incident #{self.id}"

class TelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_id = models.BigIntegerField(unique=True)

    def __str__(self):
        return self.user.username
