from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

USER_TYPE = (
    ('Vendor', 'Vendor'),
    ('Customer', 'Customer'),
)

SECURITY_QUESTIONS = (
    ('What was your childhood nickname?', 'What was your childhood nickname?'),
    ('In what city did you meet your spouse/significant other?', 'In what city did you meet your spouse/significant other?'),
    ('What is the name of your favorite childhood friend?', 'What is the name of your favorite childhood friend?'),
    ('What street did you live on in third grade?', 'What street did you live on in third grade?'),
    ('What is your oldest sibling’s birthday month and year? (e.g., January 1900)', 'What is your oldest sibling’s birthday month and year? (e.g., January 1900)'),
    ('What is the middle name of your youngest child?', 'What is the middle name of your youngest child?'),
    ('What is your oldest sibling\'s middle name?', 'What is your oldest sibling\'s middle name?'),
    ('What school did you attend for sixth grade?', 'What school did you attend for sixth grade?'),
    ('What was your childhood phone number including area code? (e.g., 000-000-0000)', 'What was your childhood phone number including area code? (e.g., 000-000-0000)'),
    ('What is your grandmother’s first name?', 'What is your grandmother’s first name?'),
)

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    is_manager = models.BooleanField(default=False)  # ✅ New field for managers
    is_vendor = models.BooleanField(default=False)  # ✅ New field for vendors

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def is_pending_vendor(self):
        """True for logged-in user who chose Vendor but isn't approved yet."""
        return (
            hasattr(self, 'vendor') and
            not self.vendor.is_approved
        )

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        email_username, _ = self.email.split('@')
        if not self.username:
            self.username = email_username
        super(User, self).save(*args, **kwargs)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images', default='default_user.png', null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    user_type = models.CharField(max_length=50, choices=USER_TYPE, null=True, blank=True, default=None)

    # Add security info for password reset
    cnic = models.CharField(max_length=15, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    security_question = models.CharField(choices=SECURITY_QUESTIONS, max_length=200, null=True, blank=True)
    security_answer = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.user.username
    
    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = self.user.username
        super(Profile, self).save(*args, **kwargs)