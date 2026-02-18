from django.db import models
import datetime
from simple_history.models import HistoricalRecords
import pgtrigger

MAX_LENGTH = 255

class Order(models.Model):
    orderitem = models.ManyToManyField(
        'shop.Good',
        through="OrderItem",
        through_fields= ("order", "good"),
        null=False,
        blank=False,
        verbose_name="Order item"
    )
    date = models.DateField(default=datetime.date.today, null=False,blank=False, verbose_name="Date")
    user = models.ForeignKey("users.User", null=False, blank=False, verbose_name="User", on_delete=models.CASCADE)
    address = models.TextField(unique=False, null=True, blank=True, verbose_name="Address")
    history = HistoricalRecords()
    isdeleted = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.orderitem} + {self.date}"
    
    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        #update change date field
        triggers = [
            pgtrigger.ReadOnly(
                name = 'read_only',
                fields=["date"]
            ),
        #Triger for soft delete
            pgtrigger.SoftDelete(
                name="soft_dlete_order",
                field="isdeleted",
                value=False
            )
        ]

class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name="OrderId", on_delete=models.CASCADE, null=False, blank=False, related_name="fk_order")
    good = models.ForeignKey("shop.Good", verbose_name="Good", null=False,blank=False,on_delete=models.CASCADE)
    user = models.ForeignKey("users.User", verbose_name="User", null=True, blank=True, on_delete=models.CASCADE)
    amount = models.IntegerField(max_length=MAX_LENGTH, null=False, verbose_name="Amount",blank=False)
    price_at_purchase = models.FloatField(max_length=MAX_LENGTH, null=True, blank=True, verbose_name="Amount")
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.order} + {self.good}"
    
    class Meta:
        verbose_name = "OrderItem"
        verbose_name_plural= "OrderItem"

