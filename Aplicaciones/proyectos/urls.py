#URLS especificas de la aplicacion
from django.urls import path
from.import views

urlpatterns = [
    # Login como inicio
    path('', views.login_usuario, name='login'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),

    path('inicio/', views.inicio, name='inicio'),
    path('nuevousuario/', views.nuevousuario),
    path('perfilusuario/',views.perfilusuario),
    path('guardarusuario/',views.guardarusuario),
    path('editarusuario/<int:id>',views.editarusuario),
    path('procesareditarusuario/', views.procesareditarusuario),  


    path('nuevovehiculo/', views.nuevovehiculo),
    path('guardarvehiculo/', views.guardarvehiculo),
    path('listadovehiculo/', views.listadovehiculo),
    path('eliminarvehiculo/<int:id>/', views.eliminarvehiculo),
    path('editarvehiculo/<int:id>/', views.editarvehiculo),
    path('procesareditarvehiculo/', views.procesareditarvehiculo),




]

