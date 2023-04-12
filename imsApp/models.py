from re import I
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from more_itertools import quantify
from django.db.models import Sum
from django.contrib.auth.models import User

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField()
    status = models.CharField(max_length=2, choices=(('1','Active'),('2','Inactive')), default=1)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name



class Product(models.Model):
    code=models.CharField(max_length=100,blank=True, null=True)
    name=models.CharField(max_length=250,blank=True, null=True)
    description = models.TextField()
    price = models.FloatField(default=0)
    status = models.CharField(max_length=2, choices=(('1','Active'),('2','Inactive')), default=1)
    image = models.ImageField(upload_to='uploads/products/',default='default_product_image.png',blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code + ' - ' + self.name

    def count_inventory(self):
        stocks = Stock.objects.filter(product = self)
        stockIn = 0
        stockOut = 0
        for stock in stocks:
            if stock.type == '1':
                stockIn = int(stockIn) + int(stock.quantity)
            else:
                stockOut = int(stockOut) + int(stock.quantity)
        available  = stockIn - stockOut
        return available



class Store(models.Model):
    name = models.CharField(max_length=250)
    address = models.TextField()
    category = models.ForeignKey(Category,on_delete=models.SET_NULL, null=True)
    products = models.ManyToManyField(Product, through='StoreProduct')
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)
    owner = models.OneToOneField(User, default=1,on_delete=models.CASCADE ,blank=True, null=True)

    def __str__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
        # Delete all associated Invoice_Item instances
        Invoice_Item.objects.filter(storeproduct__store=self).delete()
        super().delete(*args, **kwargs)

class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0)
    store = models.ForeignKey(Store,on_delete=models.SET_NULL, null=True, default=None)
    type = models.CharField(max_length=2,choices=(('1','Stock-in'),('2','Stock-Out')), default = 1)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.code + ' - ' + self.product.name

class StoreProduct(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stock = models.FloatField(default=0, blank=True, null=True)
    price = models.FloatField(default=0,blank=True, null=True)

    class Meta:
        unique_together = ["product","store"]

    def __str__(self):
        return f"{self.store.name} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        self.stock = self.count_inventory()
        super().save(*args, **kwargs)

    def count_inventory(self):
        stocks = Stock.objects.filter(product=self.product, store=self.store)
        stockIn = 0
        stockOut = 0
        # print(stocks)
        for stock in stocks:
            if stock.type == '1':
                stockIn = int(stockIn) + int(stock.quantity)
            else:
                stockOut = int(stockOut) + int(stock.quantity)
        available = stockIn - stockOut
        return available


        

class Invoice(models.Model):
    transaction = models.CharField(max_length = 250)
    customer = models.CharField(max_length = 250)
    total = models.FloatField(default= 0)
    store = models.ForeignKey(Store, on_delete=models.CASCADE,blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.transaction

    def item_count(self):
        return Invoice_Item.objects.filter(invoice = self).aggregate(Sum('quantity'))['quantity__sum']

class Invoice_Item(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    storeproduct = models.ForeignKey(StoreProduct, on_delete=models.CASCADE, blank= True, null= True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, blank= True, null= True)
    price = models.FloatField(default=0)
    quantity = models.FloatField(default=0)

    def __str__(self):
        return self.invoice.transaction


@receiver(models.signals.post_save, sender=Invoice_Item)
def stock_update(sender, instance, **kwargs):
    if instance.storeproduct:
        stock = Stock(product = instance.storeproduct.product,store= instance.storeproduct.store, quantity = instance.quantity, type = 2)
        print(stock)
        stock.save()
        StoreProduct.objects.get(pk=instance.storeproduct.id).save()
        # stockID = Stock.objects.last().id
        Invoice_Item.objects.filter(id= instance.id).update(stock=stock)

# @receiver(models.signals.post_delete, sender=Invoice_Item)
# def delete_stock(sender, instance, **kwargs):
#     try:
#         print(sender)
#         print(instance)
#         stock = Stock.objects.get(id=instance.stock.id).delete()
#     except:
#         return instance.stock.id



    
    