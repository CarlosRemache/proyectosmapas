#URLS especificas de la aplicacion
from django.urls import path
from.import views
from Aplicaciones.proyectos import views

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


    path("buscarlugares/", views.buscarlugares, name="buscarlugares"),
    path("lugar/<str:lat>/<str:lon>/", views.ver_lugar, name="ver_lugar"),
    path("guardar_lugar/<str:lat>/<str:lon>/<path:nombre>/",views.guardar_lugar,name="guardar_lugar"),
    path("eliminar_lugar/<int:id>/", views.eliminar_lugar, name="eliminar_lugar"),



    path('rutas/', views.rutas),
    path("api/ruta-optima/", views.api_ruta_optima, name="api_ruta_optima"),
    path('recorrido/', views.recorrido),
    path('historial/', views.historial, name='historial'),
    path('historial/eliminar/<int:id_ruta>/', views.eliminar_ruta_historial, name='eliminar_ruta_historial'),
 
]

