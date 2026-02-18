from django.db import models
from simple_history.models import HistoricalRecords
from django.db.models import Q
import pgtrigger
from django.db.models import Avg
from users.models import UserFavorites

MAX_LENGTH = 255

class Tag(models.Model):
    name = models.CharField(unique=True, max_length=MAX_LENGTH, null=False, blank=False, verbose_name="Tag name") 
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

class Company(models.Model):
    name = models.CharField(unique=True, max_length=MAX_LENGTH, null=False, blank=False, verbose_name="Company name")
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
    
class Type(models.Model):
    name = models.CharField(unique=True, max_length=MAX_LENGTH,null=False, blank=True, verbose_name="Type name")
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Type"
        verbose_name_plural = "Types"

class Good(models.Model):
    name = models.CharField(unique=True, max_length=MAX_LENGTH,null=False, blank=False, verbose_name="Name")
    amount = models.IntegerField(null=False, max_length=MAX_LENGTH, blank=False, verbose_name="Amount", default=0)
    cost = models.FloatField(null=False, max_length=MAX_LENGTH, blank=False, verbose_name="Cost", default=0)
    
    #Image
    image = models.ImageField(upload_to='uploads/products/')

    #characteristic
    max_voltage = models.IntegerField(null=True ,max_length=MAX_LENGTH, blank=True, verbose_name="Max voltage")
    capacity = models.IntegerField(null=True, max_length=MAX_LENGTH, blank=True, verbose_name="Capacity")
    resistance = models.IntegerField(null=True, max_length=MAX_LENGTH, blank=True, verbose_name="Resistance")

    #Foreign keys
    article = models.ForeignKey('articles.Article', null=True, blank=True, verbose_name="Article", on_delete=models.CASCADE)
    type = models.ForeignKey(Type, null=True, blank=True, verbose_name="Type", on_delete=models.CASCADE)
    company = models.ForeignKey(Company, null=True, blank=True, verbose_name="Company", on_delete=models.CASCADE)
    tag = models.ManyToManyField(Tag, null=False, blank=False, verbose_name="Tag")
    
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Good"
        verbose_name_plural = "Goods"
        constraints = [
            models.CheckConstraint(condition = models.Q(cost__gte = 0), name="Cost_must_be_greater_or_equal_0", violation_error_message="check_cost"),
            models.CheckConstraint(condition = models.Q(amount__gte = 0), name="Amount_must_be_greater_or_equal_0", violation_error_message="check_amount")
        ]
    
    def num_of_reviews(self):
        return Rate.objects.filter(good=self, isdeleted=True).count()
    
    def avg_rating(self):
        return Rate.objects.filter(good=self, isdeleted=True).aggregate(Avg('rating'))['rating__avg']
    
    def num_of_favorites(self):
        return UserFavorites.objects.filter(good=self).count()
    
class Rate(models.Model):
    good = models.ForeignKey(Good, null=True, blank=False, verbose_name="Good", on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', null=True, blank=False, verbose_name="User", on_delete=models.CASCADE)
    rating = models.FloatField(null=True, max_length=5, blank=True, verbose_name="Rating")
    comment = models.TextField(null=True, max_length=MAX_LENGTH, blank=True, verbose_name="Comment")
    isdeleted = models.BooleanField(default=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user} -> {self.good}"
    
    class Meta:
        verbose_name = "Rate"
        verbose_name_plural = "Rate"
        constraints = [
            models.CheckConstraint(condition = models.Q(rating__gte = 0), name="Value_must_be_greater_or_equal_0", violation_error_message="Rationgmustbefrom0to5")
        ]
        triggers = [
            pgtrigger.SoftDelete(
                name="soft_dlete_Rate",
                field="isdeleted",
                value=False
            )
        ]

