from django.db import transaction
from django.http import JsonResponse

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from drf_spectacular.utils import extend_schema

from konversa.mixins import PublicGenericAPIView
from integrations.email.services import BrevoEmailService

from .serializers import SignupSerializer, VerifyOTPSerializer, CustomTokenObtainPairSerializer, WaitlistSerializer
from .models import User, OTP

mailer = BrevoEmailService()

def set_refresh_cookie(response):
    data = response.data
    
    refresh = data.get("refresh")
    access = data.get("access")
    
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,    
        secure=True,      
        samesite="None"
    )

    response.data = {"data": {"access_token": access}, "detail": "Access granted", "status": "success"}
            
    return response

def health(request):
    return JsonResponse({"status": "ok"})

@extend_schema(tags=["Auth"], summary="User signup")
class SignupView(generics.CreateAPIView, PublicGenericAPIView):
    serializer_class = SignupSerializer
    
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            if not user.is_verified:
                user.delete()
                
            else:
                return Response({"email": "User with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)
                
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = serializer.save()
        otp = OTP.generate_otp(user)
        
        mailer.send_html(
            subject="Verify your email",
            template_path="emails/otp_email.html",
            recipient=user.email,
            context={"otp": otp}
        )

@extend_schema(tags=["Auth"], summary="Verify OTP for email confirmation")   
class VerifySignupOTPView(PublicGenericAPIView):  
    serializer_class = VerifyOTPSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        valid, message = serializer.otp_instance.verify(serializer.otp)
        if not valid:
            return Response({"detail": message, "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.user.is_verified = True
        serializer.user.save(update_fields=['is_verified'])
        
        response = {"detail": f"Email verified successfully, proceed to login"}
        
        return Response(response, status=status.HTTP_200_OK)
 
@extend_schema(tags=["Auth"], summary="User login")   
class LoginView(TokenObtainPairView, PublicGenericAPIView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        email = request.data.get("email").lower()
        
        if response.status_code == status.HTTP_200_OK:
            set_refresh_cookie(response)
            
            user = User.objects.filter(email=email).first()
            has_store = user.stores.exists()
            response.data["data"]["has_store"] = has_store
            
        return response
    
@extend_schema(tags=['Auth'], summary="Refresh access token")
class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        print("Refresh token from cookie:", refresh_token)
        
        if not refresh_token:
            return Response({"detail": "Session timeout, please login again"}, status=status.HTTP_401_UNAUTHORIZED)

        request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            set_refresh_cookie(response)
        
        return response

@extend_schema(tags=["Auth"], summary="Join the waitlist")   
class JoinWaitlistView(generics.CreateAPIView, PublicGenericAPIView):
    serializer_class = WaitlistSerializer
    
    @transaction.atomic()
    def perform_create(self, serializer):
        email = serializer.validated_data.get('email')
        business_name = serializer.validated_data.get('business_name')
        full_name = serializer.validated_data.get('full_name')
        
        super().perform_create(serializer)
        
        if email:
            mailer.send_html(
                subject="You're on the list!",
                template_path="emails/waitlist.html",
                recipient=email,
                context={"business_name": business_name, "full_name": full_name}
            )
            
    

    