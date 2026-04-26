from django.urls import path

from .views import SignupView, LoginView, UserProfileView, VerifySignupOTPView, JoinWaitlistView, CustomTokenRefreshView

urlpatterns = [
    path("auth/signup", SignupView.as_view(), name="signup"),
    path("auth/verify", VerifySignupOTPView.as_view(), name="verify"),
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/refresh", CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("auth/waitlist", JoinWaitlistView.as_view(), name="join-waitlist"),
    path("me", UserProfileView.as_view(), name="user-profile"),
]