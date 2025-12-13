from ast import Try
from email.mime import image
from pickle import TRUE
from django.db.models import CASCADE 
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver 
from django.db.models.signals import post_save
from django.db import connection, transaction
import cx_Oracle
import os
# adding new imports
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
# Class customer is created to extend the User model
# Attributes user are inherited by the User model
# Contain the name and email of the user
# custom imports
from django.shortcuts import render, redirect
from django.contrib import messages
# from .models import Product

class Customer(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE, null=True,blank=True, related_name = "customer")
    name=models.CharField(max_length=200,null=True)    
    email=models.CharField(max_length=200,null=True)

    def __str__(self):
        return self.name

# Class Product is created to store the products
# Attributes name, price, slug, category, digital, image, stock and stock_limit
# Method imageURL is to get the image of the product
class Product(models.Model):
    name=models.CharField(max_length=200,null=True)   
    price=models.DecimalField(max_digits=7,decimal_places=2,validators=[MinValueValidator(0.01)]) 
    slug=models.SlugField(max_length=200,default="")
    category=models.CharField(max_length=200,null=True) 
    digital=models.BooleanField(default=False,null=True,blank=True)
    image= models.ImageField(null=True,blank=True)
    stock = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    stock_limit = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])

    
    def update_price(self, new_price):
        with connection.cursor() as cursor:
            cursor.callproc('update_product_price', [self.id, new_price])
            
    def save(self, *args, **kwargs):
        if self.stock >= self.stock_limit:
            raise ValidationError("Stock must be lower than stock limit")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        try:
            url=self.image.url
        except: 
            url=''
        return url


# Class Order is created to store the orders
# Attributes customer, date_ordered, complete, transaction_id
# Metods get_cart_total, get_cart_items and shipping are to get the total, the items and the shipping of the order
class Order(models.Model):
    #a single customer can have multiple orders
    customer = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    order_day = models.DateField(auto_now_add=True, null= True)
    complete=models.BooleanField(default=False,null=True,blank=False)
    transaction_id=models.CharField(max_length=100,null=True)  
    total_money = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        if self.customer is not None:
            return str(self.customer)
        return "Unknown"
   
    '''xử lí mức lập trình'''
    @property
    def get_cart_total_(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        self.total_money = total
        self.save()
        return total 

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total  
    
    '''store procedure'''
    @property
    def get_cart_total(self):
        try:
            cursor = connection.cursor()
            # Gọi hàm calculate_cart_total và nhận kết quả trả về
            result = cursor.callfunc("calculate_cart_total", cx_Oracle.NUMBER, [self.id])
            
            print('------------------------------------------------')
            print('Đây là số tiền mà dự kiến Quyên phải trả: ', result)
            print('------------------------------------------------')
            
            # Cập nhật total_money với giá trị tính được
            self.total_money = result
            self.save()

            return self.total_money

        except cx_Oracle.DatabaseError as e:
            # Xử lý lỗi kết nối Oracle
            error, = e.args
            print(f"Oracle error code: {error.code}")
            print(f"Oracle error message: {error.message}")
        finally:
            # Đảm bảo đóng cursor sau khi hoàn thành
            cursor.close()

    
    @property
    def shipping(self):
        shipping=False
        orderitems = self.orderitem_set.all()
        for i in orderitems:
            if i.product.digital == False:
                shipping=True
            return shipping
        
    def save(self, *args, **kwargs):
     if self.complete:
        order_items = self.orderitem_set.all()
        for item in order_items:
            if item.product is not None:
                #item.product.stock -= item.quantity
                item.product.save()
     super().save(*args, **kwargs)



# Class OrderItem is created to detailed the order
# Attributes product, order, quantity and date_added
# Metod get_total is to get the total of the order
class OrderItem (models.Model):
    product = models.ForeignKey(Product,on_delete=models.SET_NULL,null=True,blank=True)
    order = models.ForeignKey(Order,on_delete=models.CASCADE,null=True,blank=True)
    quantity = models.IntegerField(default=0,null=True,blank=True, validators=[MinValueValidator(0)])
    date_added = models.DateTimeField(auto_now_add=True)
    
    @property
    def get_total(self):
        if self.product is not None:
            total = self.product.price * self.quantity
            return total
        return 0
    
    def save(self, *args, **kwargs):
        #if self.product is not None:
         #   if self.product.stock - self.quantity < 0:
          #      raise ValidationError("quantity must lower than stock")
           # self.product.save()
        super(OrderItem, self).save(*args, **kwargs) #super().save(*args, **kwargs)



# Class ShippingAddress is created to store the shipping address
# Attributes customer, order, name, address, city, state, zipcode and date_added
class ShippingAddress (models.Model):
    customer = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True, related_name='addresse')
    order = models.ForeignKey(Order,on_delete=models.SET_NULL,null=True,blank=True)
    name=models.CharField(max_length=200,null=True)   
    address=models.CharField(max_length=200,null=True)   
    city=models.CharField(max_length=200,null=True)   
    state=models.CharField(max_length=200,null=True)   
    zipcode=models.CharField(max_length=200,null=True)   
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address


# Class post use to store the post in the blog
# Attributes title, description, slug, date_posted and image
class Post(models.Model):
    title=models.CharField(max_length=200,null=True)   
    description=models.CharField(max_length=800,null=True) 
    slug=models.SlugField(max_length=200,default="")   
    date_posted = models.DateTimeField(auto_now_add=True)
    image= models.ImageField(null=True,blank=True)

    def __str__(self):
        return self.title
        
    @property
    def imageURL(self):
        try:
            url=self.image.url
        except: 
            url=''
        return url


# Class Comment is created to store the comments in the blog
# Attributes post, name, body and date_commented
class Comment(models.Model):
    post=models.ForeignKey(Post,related_name="comments",on_delete=models.CASCADE)
    name=models.CharField(max_length=200)
    body=models.TextField(max_length=200)
    date_commented=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s - %s' % (self.post.title,self.name)


# Func create_user_customer is created to create a customer when a user is created
# It is called when a user is created and create an instance of customer
@receiver(post_save, sender=User)
def create_user_customer(sender, instance, created, **kwargs):
	print('****', created)
	if instance.is_staff == False:
		Customer.objects.get_or_create(user = instance, name = instance.username, email = instance.email)


import json
import time
from kafka import KafkaProducer
import logging

# Cấu hình Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SalesProducer:
    def __init__(self, bootstrap_servers=None):
        if bootstrap_servers is None:
            bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Đảm bảo Kafka đã nhận được tin
                retries=3
            )
            logger.info("Kafka Producer connected successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.producer = None

    def send_order(self, order_data):
        """
        Gửi dữ liệu đơn hàng vào Kafka topic 'sales_transactions'
        
        Expected order_data format:
        {
            "transaction_id": "T123",
            "product_id": "P001",
            "quantity": 2,
            "price": 100.0,
            "timestamp": 1715421000000, (Unix ms)
            "customer_id": 1
        }
        """
        if not self.producer:
            logger.warning("Kafka Producer is not available. Skipping message.")
            return

        try:
            topic = 'sales_transactions'
            # Gửi bất đồng bộ (fire and forget)
            future = self.producer.send(topic, order_data)
            # Chờ xác nhận (chỉ dùng khi debug, production nên bỏ dòng này để nhanh)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Sent to Kafka topic {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
            print(f"[Kafka] Sent Order: {order_data['transaction_id']}")
            
        except Exception as e:
            logger.error(f"Error sending data to Kafka: {e}")

# Helper function để gọi nhanh từ Django View
# Usage: 
# from kafka_service import send_order_to_kafka
# send_order_to_kafka(transaction_id, product_id, quantity, price, customer_id)

producer_instance = SalesProducer()

def send_order_to_kafka(transaction_id, product_id, quantity, price, customer_id):
    data = {
        "transaction_id": str(transaction_id),
        "product_id": str(product_id),
        "quantity": int(quantity),
        "price": float(price),
        "timestamp": int(time.time() * 1000), # Current time in ms
        "customer_id": int(customer_id)
    }
    producer_instance.send_order(data)
