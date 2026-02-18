from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords

MAX_LENGTH = 255

class Role(models.Model):
    rolename = models.CharField(unique=True, max_length=MAX_LENGTH)

    def __str__(self):
        return self.rolename
    
        
    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = "Roles"

#Best way to create your user
class User(AbstractUser):
    email = models.EmailField(unique=True, null=True, max_length=MAX_LENGTH, blank=True, verbose_name="Email")
    bonus = models.DecimalField(null=False, blank=False, default=0.0, decimal_places=2, max_digits=10, verbose_name="Bouns")
    role = models.ForeignKey( Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Role") 
    history = HistoricalRecords()
   
    favorites = models.ManyToManyField(
        'shop.Good',
        through="UserFavorites",
        through_fields=("user", "good"),
        verbose_name="Favorite",
        blank=True,
        null=True,
    )
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = "Users"
    
    def __str__(self):
        return self.username
    
class UserPreference(models.Model):
    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
        ("gold", "Gold"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preference")
    theme = models.CharField(max_length=16, choices=THEME_CHOICES, default="light")
    date_format = models.CharField(max_length=32, default="%Y-%m-%d")
    page_size = models.PositiveIntegerField(default=12)
    saved_filters = models.JSONField(default=dict, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user.username} preferences"


@receiver(post_save, sender=User)
def ensure_user_preferences(sender, instance, created, **kwargs):
    if created:
        UserPreference.objects.create(user=instance)

class UserCredenetials(models.Model):
    user = models.OneToOneField(User, null=False, blank=False,verbose_name="User", on_delete=models.CASCADE)
    humanname = models.CharField(unique=True, null=True, max_length=MAX_LENGTH,blank=True, verbose_name="User real name")
    phonenumber = models.CharField(unique=True, null=True, max_length=14, blank=True, verbose_name="Phone number")
    history = HistoricalRecords()

    def __str__(self):
        return self.humanname
    
    class Meta:
        verbose_name = 'User Credential'
        verbose_name_plural = "User Credentials"    

#to try define own many to manyField
class UserFavorites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, verbose_name="User")
    good = models.ForeignKey('shop.Good', on_delete=models.CASCADE, null=False, verbose_name="Good")
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user} + {self.good}"  
    
    class Meta:
        verbose_name = "User favorite"
        verbose_name_plural = "User favorites"
