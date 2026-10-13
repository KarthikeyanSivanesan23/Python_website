from django.urls import path
from . import views

urlpatterns = [
    path('session/', views.session), path('auth/<str:action>/', views.auth), path('readiness/', views.readiness),
    path('database-readiness/', views.database_readiness),
    path('curriculum/', views.curriculum), path('lessons/<slug:slug>/', views.lesson),
    path('exercises/<slug:slug>/draft/', views.draft), path('exercises/<slug:slug>/submit/', views.submit),
    path('exercises/<slug:slug>/reveal/<str:kind>/', views.reveal), path('exercises/<slug:slug>/mentor/', views.conversation),
    path('progress/<slug:slug>/', views.progress), path('dashboard/', views.dashboard),
]
