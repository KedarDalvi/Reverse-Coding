from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.signup, name='signup'),
    path('SignIn/',views.signin, name='signin'),
    path('logout/',views.logout, name='logout'),
    path('quiz/',views.quiz, name='quiz'),
    path('quiz_post/',views.quiz_post,name='quiz_post'),
    path('signup_validation/', views.username_validation, name='signup_validation'),
    path('SignIn/signin_validation/', views.signin_validation, name='signin_validation'),
    path('emergencylogin/', views.emergencylogin, name='emergencylogin'),
    path('hot_or_cold/', views.hot_or_cold, name='hot_or_cold'),
    path('extra_time/', views.extra_time, name='extra_time'),
    ]

