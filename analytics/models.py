from django.db import models
from simple_history.models import HistoricalRecords
from cart.models import Order
import pgtrigger
MAX_LENGTH = 255

#Views
class UserOrders(models.Model):
    adress = models.CharField(db_column="user_adres", max_length=MAX_LENGTH)
    email = models.EmailField(db_column="user_email", max_length=MAX_LENGTH, primary_key=True)
    phonenumber = models.TextField(db_column="user_phonenumber", max_length=MAX_LENGTH)
    date = models.DateField(db_column="cart_date",max_length=MAX_LENGTH)
    
    class Meta:
        managed = False
        db_table = 'user_orders'
        
class GoodIncome(models.Model):
    custom_id = models.IntegerField(primary_key=True)
    user = models.CharField(db_column="users_income", max_length=255)
    date = models.DateField(db_column="date_income")
    orders = models.FloatField(db_column="orders_income")

    class Meta:
        managed = False
        db_table = "good_icome"


class DangerousGoods(models.Model):
    dangerous_good = models.IntegerField(db_column="id", primary_key=True)
    good = models.CharField(db_column="good_name", max_length=MAX_LENGTH)
    amount = models.CharField(db_column="good_amount", max_length=MAX_LENGTH)
    
    class Meta:
        managed = False
        db_table = "dangerous_goods"

class OrderReport(models.Model):
    order_id = models.IntegerField(primary_key=True, db_column="order_id")
    date = models.DateField(db_column="order_date", )
    username = models.CharField(db_column="username")
    product_name = models.CharField(db_column="product_name")
    price_at_purchase = models.DecimalField(db_column="price_at_purchase", decimal_places=2, max_digits=MAX_LENGTH)
    total = models.DecimalField(db_column="total", decimal_places=2, max_digits=MAX_LENGTH)
    
    class Meta:
        managed = False
        db_table = "orders_report"
