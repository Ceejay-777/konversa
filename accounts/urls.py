from django.urls import path

from .views import SignupView, LoginView, VerifySignupOTPView, JoinWaitlistView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("verify/", VerifySignupOTPView.as_view(), name="verify"),
    path("login/", LoginView.as_view(), name="login"),
    path("waitlist/", JoinWaitlistView.as_view(), name="join-waitlist"),
]