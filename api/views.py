from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Soldier
import logging
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import Equipment, InventoryLog
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    InventoryItemSerializer,
    InventoryLogSerializer
)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from datetime import datetime
from django.db import IntegrityError

logger = logging.getLogger(__name__)
User = get_user_model()



class PingView(APIView):
    permission_classes = [permissions.AllowAny]  # Allow unauthenticated access
    
    def get(self, request):
        return Response({"status": "API is working"}, status=status.HTTP_200_OK)



class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    @action(detail=False, methods=['post', 'get'])
    def register(self, request):
        if request.method == 'GET':
            return Response({
                "message": "Please send a POST request with registration details",
                "required_fields": {
                    "username": "string (required)",
                    "password": "string (required)",
                    "confirm_password": "string (required, must match password)",
                    "full_name": "string (required)",
                    "rank": "string (required)",
                    "unit": "string (required)",
                    "phone_number": "string (digits only)",
                    "birth_date": "YYYY-MM-DD or DD/MM/YYYY or MM/DD/YYYY",
                    "role": "string (one of: Civilian Employee, Military Personnel, Contractor)",
                },
                "content_type": "multipart/form-data required for file upload"
            })

        try:
            # Convert date format if needed
            if 'birth_date' in request.data:
                try:
                    date_str = request.data['birth_date']
                    # Try different date formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    return Response({
                        'error': 'Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY',
                        'field': 'birth_date'
                    }, status=status.HTTP_400_BAD_REQUEST)

            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'token': str(refresh.access_token),
                    'user': UserSerializer(user).data,
                    'message': 'Registration successful'
                }, status=status.HTTP_201_CREATED)
            
            # Return detailed validation errors
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except IntegrityError as e:
            # Check if the error is due to the unique id_code constraint
            if 'id_code' in str(e):
                return Response({
                    'error': 'Registration failed',
                    'message': 'A user with this QR ID already exists.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Handle other integrity errors
                return Response({
                    'error': 'Registration failed',
                    'message': 'Database integrity error: ' + str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) # Use 500 for unexpected server errors
        except Exception as e:
            return Response({
                'error': 'Registration failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'user': UserSerializer(user).data
        })

    @action(detail=False, methods=['post'])
    def login_qr(self, request):
        id_code = request.data.get('id_code')
        try:
            user = User.objects.get(id_code=id_code)
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        except User.DoesNotExist:
            return Response({'error': 'Invalid ID code'}, status=status.HTTP_401_UNAUTHORIZED)

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class InventoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventoryItemSerializer
    queryset = Equipment.objects.all()

    def get_queryset(self):
        return Equipment.objects.filter(assigned_to=self.request.user)

    @action(detail=False, methods=['post'])
    def scan(self, request):
        qr_code = request.data.get('qr_code')
        try:
            item = Equipment.objects.get(qr_code=qr_code)
            
            if item.status == 'available' and not item.assigned_to:
                item.status = 'withdrawn'
                item.assigned_to = request.user
                item.save()
                
                InventoryLog.objects.create(
                    item=item,
                    user=request.user,
                    action='withdraw'
                )
                
                return Response(self.get_serializer(item).data)
            elif item.status == 'withdrawn' and item.assigned_to == request.user:
                item.status = 'available'
                item.assigned_to = None
                item.save()
                
                InventoryLog.objects.create(
                    item=item,
                    user=request.user,
                    action='return'
                )
                
                return Response(self.get_serializer(item).data)
            else:
                return Response(
                    {'error': 'Item is not available or not assigned to you'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Equipment.DoesNotExist:
            return Response(
                {'error': 'Invalid QR code'},
                status=status.HTTP_404_NOT_FOUND
            )

class InventoryLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventoryLogSerializer

    def get_queryset(self):
        return InventoryLog.objects.filter(user=self.request.user).order_by('-timestamp')
