from django.conf import settings
from decimal import Decimal
from shop.models import Good

class Cart(object):
    def __init__(self, request):
        #initializing cart
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def save(self):
        self.session.modified = True
    
    def add(self, good, amount=1, override_quantity=False):
        good_id = str(good.id)
        if good_id not in self.cart:
            self.cart[good_id] = {
                'amount': 0,
                'price_at_purchase': str(good.cost),
            }
        if good.amount <= 0:
            if good_id in self.cart:
                del self.cart[good_id]
                self.save()
            return
        amount = int(amount)
        if override_quantity:
            amount = max(amount, 1)
            amount = min(amount, good.amount)
            self.cart[good_id]['amount'] = amount
        else:
            new_amount = self.cart[good_id]['amount'] + amount
            new_amount = max(new_amount, 1)
            new_amount = min(new_amount, good.amount)
            self.cart[good_id]['amount'] = new_amount
        self.save()
    
    def remove(self,good):
        good_id = str(good.id)
        
        if good_id in self.cart:
            del self.cart[good_id]
        self.save()
    
    def __iter__(self):
        #Loop throught cart items and fetch the products from the database
        good_ids = self.cart.keys()
        # get the product objects and add them to the cart
        goods = Good.objects.filter(id__in=good_ids)
        cart = self.cart.copy()
        for good in goods:
            cart[str(good.id)]['good'] = good
        for item in cart.values():
            item['price_at_purchase'] = Decimal(item['price_at_purchase'])
            item['total_price'] = item['price_at_purchase'] * item['amount']
            yield item 
            
    def __len__(self):
        return sum(item['amount'] for item in self.cart.values())
    
    def get_total_price(self):
        return sum(
            Decimal(item["price_at_purchase"]) * item["amount"]
            for item in self.cart.values()
        )
    
    def clear(self):
        #revove cart form session
        del self.session[settings.CART_SESSION_ID]
        self.save()
