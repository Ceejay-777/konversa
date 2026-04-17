from rest_framework import serializers
from .models import User, OTP, PlatformChoices, WaitList

from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["sqid", "email", "password", "username"]
        read_only_fields = ["sqid"]

    def create(self, validated_data):
         validated_data['is_verified'] = False
        
         user = super().create(validated_data)
         return user
     
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, write_only=True, min_length=6, max_length=6)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get("email")
        otp = validated_data.get("otp")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email"})
        
        try:
            otp_instance = user.otp
        except OTP.DoesNotExist:
           raise serializers.ValidationError({"otp": "No OTP found"})

        self.user = user
        self.otp_instance = otp_instance
        self.otp = otp
        
        return validated_data
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_verified:
            raise exceptions.PermissionDenied(
                detail="Your email is not verified. Please verify your email to continue.",
                code="email_unverified"
            )
            
        return data
    
class WaitlistSerializer(serializers.ModelSerializer):
    platforms = serializers.ListField(child=serializers.ChoiceField(choices=PlatformChoices.choices), required=False) 
    
    class Meta:
        model = WaitList
        fields = ["sqid", "email", "full_name", "business_name", "platforms", "phone_number", "created_at"]
        read_only_fields = ["sqid", "created_at"]
   
    def validate_phone_number(self, value):
        if WaitList.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        
        return value 