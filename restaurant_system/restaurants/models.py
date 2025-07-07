from django.db import models
from django.contrib.auth.models import User

class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('APP', 'Appetizer'),
        ('MAIN', 'Main Course'),
        ('DES', 'Dessert'),
        ('BEV', 'Beverage'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    preparation_time = models.PositiveIntegerField()  # in minutes
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Table(models.Model):
    TABLE_STATUS = [
        ('AV', 'Available'),
        ('OC', 'Occupied'),
        ('RS', 'Reserved'),
        ('MA', 'Maintenance'),
    ]
    number = models.CharField(max_length=4, unique=True)
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=2, choices=TABLE_STATUS, default='AV')
    location = models.CharField(max_length=50)  # e.g., "Window", "Patio"

    def __str__(self):
        return f"Table {self.number} ({self.capacity} seats)"

class Reservation(models.Model):
    customer_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField()
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    party_size = models.PositiveIntegerField()
    reservation_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    special_requests = models.TextField(blank=True)

    def __str__(self):
        return f"Reservation for {self.customer_name} at {self.reservation_time}"

class Order(models.Model):
    ORDER_STATUS = [
        ('P', 'Pending'),
        ('C', 'Cooking'),
        ('R', 'Ready'),
        ('S', 'Served'),
        ('X', 'Cancelled'),
    ]
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=1, choices=ORDER_STATUS, default='P')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_takeaway = models.BooleanField(default=False)

    def calculate_total(self):
        return sum(item.subtotal() for item in self.orderitem_set.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    special_requests = models.TextField(blank=True)

    def subtotal(self):
        return self.menu_item.price * self.quantity

class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20)  # e.g., 'kg', 'liters', 'pieces'
    current_stock = models.DecimalField(max_digits=8, decimal_places=2)
    alert_threshold = models.DecimalField(max_digits=8, decimal_places=2)
    supplier = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"

class Recipe(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity_required = models.DecimalField(max_digits=6, decimal_places=2)

class StaffUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('WAITER', 'Waiter'),
        ('CHEF', 'Chef'),
        ('MANAGER', 'Manager'),
        ('ADMIN', 'Admin')
    ])
    pin_code = models.CharField(max_length=4)

    def __str__(self):
        return f"{self.user.username} ({self.role})"