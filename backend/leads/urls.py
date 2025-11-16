from django.urls import path

from .views import LandingPageView, SubmitLeadView, health_check

urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
    path("api/leads/", SubmitLeadView.as_view(), name="submit_lead"),
    path("api/health/", health_check, name="health_check"),
]
