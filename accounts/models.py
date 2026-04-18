from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django_sqids import SqidsField
from django.utils import timezone
from datetime import timedelta
from konversa.models import BaseModel
from konversa.utils import generate_otp

def default_expiry():
    return timezone.now() + timedelta(minutes=10)

class UserManager(BaseUserManager):
    def create_user(self, **extra_fields):
        email = extra_fields.get("email")
        password = extra_fields.pop("password", None)
        
        email = self.normalize_email(email).lower()
        extra_fields["email"] = email
        
        user = self.model(**extra_fields)
        if password:
            user.set_password(password)
            
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        email = extra_fields.get("email")
        email = self.normalize_email(email).lower()
        extra_fields["email"] = email
        
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    sqid = SqidsField(real_field_name="id", min_length=7)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    objects = UserManager()

    def __str__(self):
        return self.email
    
class OTP(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="otp")
    otp = models.CharField(max_length=6)  
    expiry = models.DateTimeField(default=default_expiry)
    verified = models.BooleanField(default=False)
    
    @classmethod
    def generate_otp(cls, user, expiry_minutes=10):
        """Create or replace OTP for a user"""
        otp = generate_otp()
        expiry_time = timezone.now() + timedelta(minutes=expiry_minutes)

        otp, _ = cls.objects.update_or_create(
            user=user,
            defaults={
                "otp": otp,
                "expiry": expiry_time,
                "verified": False
            }
        )
        return otp

    def is_expired(self):
        return timezone.now() > self.expiry

    def verify(self, otp):
        if self.verified:
            return False, "OTP already used"

        if self.is_expired():
            return False, "This OTP has expired"

        if self.otp != otp:
            return False, "Invalid OTP"

        self.verified = True
        self.save(update_fields=["verified"])
        return True, "OTP verified successfully"
    
    def __str__(self):
        return self.otp
    
class PlatformChoices(models.TextChoices):
    INSTAGRAM = 'instagram', 'Instagram'
    TIKTOK = 'tiktok', 'TikTok'
    WHATSAPP = 'whatsapp', 'WhatsApp'
    TELEGRAM = 'telegram', 'Telegram'
    
class WaitList(BaseModel):
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True,blank=True, null=True)
    full_name = models.CharField(max_length=255)
    business_name = models.CharField(max_length=255, blank=True, null=True)
    platforms = models.JSONField(default=list)

    def __str__(self):
        return self.full_name