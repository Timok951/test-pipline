from django.db import models
from simple_history.models import HistoricalRecords

MAX_LENGTH = 255

class Article (models.Model):
    name = models.TextField(unique=True, blank=False, null=False, max_length=MAX_LENGTH)
    text = models.TextField(blank=False, max_length=MAX_LENGTH, null=False)
    image = models.ImageField(blank=True, null=True, upload_to='uploads/articles')
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"

