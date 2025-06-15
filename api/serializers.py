from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Equipment, InventoryLog

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'full_name', 'rank', 'unit', 'id_code')
        read_only_fields = ('id',)

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    birth_date = serializers.DateField(format='%Y-%m-%d', input_formats=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'])

    class Meta:
        model = User
        fields = (
            'username', 'password', 'confirm_password', 'full_name',
            'rank', 'unit', 'id_code', 'phone_number', 'birth_date',
            'role', 'email'
        )

    def validate(self, data):
        # Password validation
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match"
            })

        # Phone number validation (basic)
        phone = data.get('phone_number')
        if phone and not phone.isdigit():
            raise serializers.ValidationError({
                "phone_number": "Phone number should contain only digits"
            })

        # Role validation
        valid_roles = ['Civilian Employee', 'Military Personnel', 'Contractor']
        if data.get('role') and data['role'] not in valid_roles:
            raise serializers.ValidationError({
                "role": f"Role must be one of: {', '.join(valid_roles)}"
            })

        # Required fields validation
        required_fields = ['username', 'password', 'full_name', 'rank', 'unit', 'email']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError({
                    field: f"{field.replace('_', ' ').title()} is required"
                })

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        if not validated_data.get('id_code'):
            import uuid
            validated_data['id_code'] = str(uuid.uuid4())
        try:
            user = User.objects.create_user(**validated_data)
            return user
        except Exception as e:
            raise serializers.ValidationError({
                "error": str(e)
            })

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ('id', 'name', 'category', 'qr_code', 'qr_string', 'status', 'assigned_to')
        read_only_fields = ('id',)

class InventoryLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    item = InventoryItemSerializer(read_only=True)

    class Meta:
        model = InventoryLog
        fields = ('id', 'item', 'user', 'action', 'timestamp', 'notes')
        read_only_fields = ('id', 'timestamp') 