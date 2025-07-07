from rest_framework import serializers
from .models import *
from .models import StaffProfile, MenuItem, Table, OrderItem, Order, Reservation, Ingredient

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'quantity', 'special_requests']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ['id', 'table', 'status', 'created_at', 'total_price', 'is_takeaway', 'items']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'
        extra_kwargs = {
            'reservation_time': {'input_formats': ['%Y-%m-%dT%H:%M']}
        }

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ['user', 'role', 'pin_code']