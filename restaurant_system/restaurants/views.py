from rest_framework import generics, status, permissions
from rest_framework.response import Response
from .models import *
from .serializers import *
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F
from datetime import date, timedelta
from django_filters.rest_framework import DjangoFilterBackend

# Menu Views
class MenuListAPI(generics.ListAPIView):
    queryset = MenuItem.objects.filter(is_available=True)
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']

# Table Views
class TableListAPI(generics.ListAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer

class TableAvailabilityAPI(generics.GenericAPIView):
    serializer_class = TableAvailabilitySerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        party_size = serializer.validated_data['party_size']
        start_time = serializer.validated_data['start_time']
        duration = timedelta(hours=2)
        
        conflicting_reservations = Reservation.objects.filter(
            reservation_time__range=(start_time, start_time + duration)
        ).values_list('table', flat=True)
        
        available_tables = Table.objects.filter(
            capacity__gte=party_size,
            status='AV'
        ).exclude(id__in=conflicting_reservations)
        
        return Response({
            'available_tables': TableSerializer(available_tables, many=True).data
        })

# Order Views
class OrderCreateAPI(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):
        order = serializer.save()
        
        # Calculate total price
        total = 0
        for item in order.items.all():
            total += item.menu_item.price * item.quantity
        order.total_price = total
        order.save()
        
        # Update inventory
        for order_item in order.items.all():
            recipe_requirements = Recipe.objects.filter(menu_item=order_item.menu_item)
            for requirement in recipe_requirements:
                ingredient = requirement.ingredient
                ingredient.current_stock -= requirement.quantity_required * order_item.quantity
                ingredient.save()

class OrderStatusUpdateAPI(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        order = serializer.save()
        # Add notifications/kitchen display logic here

# Reservation Views
class ReservationCreateAPI(generics.CreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    
    def perform_create(self, serializer):
        reservation = serializer.save()
        reservation.table.status = 'RS'
        reservation.table.save()

# Inventory Views
class InventoryListAPI(generics.ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = InventorySerializer

class LowStockAlertAPI(generics.ListAPIView):
    serializer_class = InventorySerializer
    queryset = Ingredient.objects.filter(current_stock__lt=F('alert_threshold'))

# Reporting Views
class DailySalesReportAPI(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        today = date.today()
        orders = Order.objects.filter(
            created_at__date=today,
            status__in=['S', 'R']
        )
        
        total_sales = orders.aggregate(total=Sum('total_price'))['total'] or 0.00
        
        popular_items = OrderItem.objects.filter(
            order__created_at__date=today
        ).values('menu_item__name').annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:5]
        
        return Response({
            'date': today,
            'total_sales': total_sales,
            'popular_items': list(popular_items)
        })

# Authentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'role': user.staffprofile.role if hasattr(user, 'staffprofile') else None
        })