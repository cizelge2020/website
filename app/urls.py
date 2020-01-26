from django.urls import path
from .views import home,form,schedule
urlpatterns = [
    path('', home),
    path('form', form),
    path('schedule', schedule),
]
