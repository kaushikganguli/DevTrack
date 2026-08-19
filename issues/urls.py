from django.urls import path
from .views import reporters, issues

urlpatterns = [
    path("reporters/", reporters, name="reporters"),
    path("issues/", issues, name="issues"),
]