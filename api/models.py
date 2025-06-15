import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    ROLE_CHOICES = [
        ('Civilian Employee', 'Civilian Employee'),
        ('Military Personnel', 'Military Personnel'),
        ('Contractor', 'Contractor'),
    ]

    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(max_length=255)
    rank = models.CharField(max_length=100)
    unit = models.CharField(max_length=100)
    id_code = models.CharField(
        max_length=100,
        unique=True,
        default=uuid.uuid4,  # Automatically generates unique code
        editable=False
    )
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Civilian Employee')
    id_type = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.role})"


class Soldier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='soldier_profile', null=True, blank=True)
    id_number = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_registered = models.DateTimeField(default=timezone.now)

    guns = models.TextField(blank=True, default="")
    ammos = models.TextField(blank=True, default="")
    explosives = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id_number})"


class Equipment(models.Model):
    CATEGORY_CHOICES = [
        ('gun', 'Gun'),
        ('ammo', 'Ammo'),
        ('explosive', 'Explosive'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('withdrawn', 'Withdrawn'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_string = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_equipment'
    )

    def save(self, *args, **kwargs):
        if not self.qr_string:
            self.qr_string = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class InventoryLog(models.Model):
    ACTION_CHOICES = [
        ('withdraw', 'Withdraw'),
        ('return', 'Return'),
    ]

    item = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_logs'

    def __str__(self):
        return f"{self.user.username} {self.action} {self.item.name} at {self.timestamp}"
