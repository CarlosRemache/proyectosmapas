from django.urls import path
from.import views
from .views import ManifestView, ServiceWorkerView, offline


urlpatterns = [
    # Login como inicio
    path('', views.login_usuario, name='login'),
    path('login/', views.login_usuario),
    path('logout/', views.logout_usuario, name='logout'),
    path('adminpanel/', views.admin_panel, name='admin_panel'),

    #usuario
    path('inicio/', views.inicio, name='inicio'),
    path('nuevousuario/', views.nuevousuario),
    path('perfilusuario/',views.perfilusuario),
    path('guardarusuario/',views.guardarusuario),
    path('editarusuario/<int:id>',views.editarusuario),
    path('procesareditarusuario/', views.procesareditarusuario),
    path('listadousuario/', views.listadousuario),  
    #documento
    path('creardocumento/', views.creardocumento, name='creardocumento'),

    #vehiculo
    path('nuevovehiculo/', views.nuevovehiculo),
    path('guardarvehiculo/', views.guardarvehiculo),
    path('listadovehiculo/', views.listadovehiculo),
    path('eliminarvehiculo/<int:id>/', views.eliminarvehiculo),
    path('editarvehiculo/<int:id>/', views.editarvehiculo),
    path('procesareditarvehiculo/', views.procesareditarvehiculo),

    #lugares del mapa
    path("buscarlugares/", views.buscarlugares, name="buscarlugares"),
    path("lugar/<str:lat>/<str:lon>/", views.ver_lugar, name="ver_lugar"),
    path("guardar_lugar/<str:lat>/<str:lon>/<path:nombre>/",views.guardar_lugar,name="guardar_lugar"),
    path("eliminar_lugar/<int:id>/", views.eliminar_lugar, name="eliminar_lugar"),

    #rutas
    path('rutas/', views.rutas, name='rutas'),
    path("api/ruta-optima/", views.api_ruta_optima, name="api_ruta_optima"),
    path('recorrido/', views.recorrido),
    path('historial/', views.historial, name='historial'),
    path('historial/eliminar/<int:id_ruta>/', views.eliminar_ruta_historial, name='eliminar_ruta_historial'),

    #calendario
    path('panel/calendario/', views.admin_calendario, name='admin_calendario'),
    path('panel/calendario/eventos/', views.admin_eventos_json, name='admin_eventos_json'),
    path('panel/calendario/crear/', views.admin_evento_crear, name='admin_evento_crear'),
    path('panel/calendario/lista/', views.listar_eventos_admin, name='lista_eventos_admin'),
    path('panel/calendario/editar/<int:id_evento>/', views.editar_evento_admin, name='editar_evento_admin'),
    path('panel/calendario/eliminar/<int:id_evento>/', views.eliminar_evento_admin, name='eliminar_evento_admin'),
    #asignar al calendario
    path('lista_asignaciones/', views.lista_asignaciones, name='lista_asignaciones'),
    path('crear_asignacion/', views.crear_asignacion, name='crear_asignacion'),
    path('asignaciones/editar/<int:id>/', views.editar_asignacion, name='editar_asignacion'),
    path('asignaciones/eliminar/<int:id>/', views.eliminar_asignacion, name='eliminar_asignacion'),

    #agregar provedor
    path('listadoproveedor/', views.listadoproveedor),
    path('nuevoproveedor/', views.nuevoproveedor),
    path('guardarproveedor/', views.guardarproveedor),
    path('eliminarproveedor/<int:id>/', views.eliminarproveedor),
    path('editarproveedor/<int:id>/', views.editarproveedor),
    path('procesareditarproveedor/', views.procesareditarproveedor),

    #pedidos
    path('listadopedido/', views.listadopedido, name='listadopedido'),
    path('nuevopedido/', views.nuevopedido, name='nuevopedido'),
    path('guardarpedido/', views.guardarpedido, name='guardarpedido'),
    path('editarpedido/<int:id>/', views.editarpedido, name='editarpedido'),
    path('procesareditarpedido/', views.procesareditarpedido, name='procesareditarpedido'),
    path('eliminarpedido/<int:id>/', views.eliminarpedido, name='eliminarpedido'),


    #detalles del pedido
    path('listadodetalle/<int:id_pedido>/', views.listadodetalle, name='listadodetalle'),
    path('nuevodetalle/<int:id_pedido>/', views.nuevodetalle, name='nuevodetalle'),
    path('guardardetalle/', views.guardardetalle, name='guardardetalle'),
    path('editardetalle/<int:id>/', views.editardetalle, name='editardetalle'),
    path('procesareditardetalle/', views.procesareditardetalle, name='procesareditardetalle'),
    path('eliminardetalle/<int:id>/', views.eliminardetalle, name='eliminardetalle'),
    path("agregarproducto/", views.seleccionar_pedido_detalle, name="agregarproducto"),
    path("redirigir_detalle/lista/", views.redirigir_detalle_lista, name="redirigir_detalle_lista"),
    path("redirigir_detalle/nuevo/", views.redirigir_detalle_nuevo, name="redirigir_detalle_nuevo"),

    #notificacion
    path('pedidosusuario/', views.pedidosusuario, name='pedidosusuario'),
    path('panel/usuario/eventos/', views.usuario_eventos_json, name='usuario_eventos_json'),
    path("panel/notificacion/evento/", views.usuario_toast_evento, name="usuario_toast_evento"),
    path("usuario/asignacion/<int:asig_id>/estado/", views.usuario_cambiar_estado, name="usuario_cambiar_estado"),
    path("panel/asignaciones/reporte/", views.reporte_asignaciones, name="reporte_asignaciones"),

    #reportes
    path('reporteviaje/', views.reporteviaje, name='reporteviaje'),
    path('reportehistorial/', views.reportehistorial, name='reportehistorial'),



    path('verificar_registro/', views.verificar_registro, name='verificar_registro'),


    #factura
    path('nuevafactura/', views.nuevafactura, name='nuevafactura'),
    path('crear_factura/', views.crear_factura, name='crear_factura'),
    path('ver_factura/<int:id_factura>/', views.ver_factura, name='ver_factura'),
    path('listadofacturas/', views.listado_facturas, name='listado_facturas'),
    path('eliminarfactura/<int:id>/', views.eliminar_factura, name='eliminar_factura'),
    path('factura/pdf/<int:id_factura>/', views.factura_pdf, name='factura_pdf'),


    #salvoconducto
    path('salvoconductos/', views.salvoconductos, name='salvoconductos'),
    path('nuevosalvoconducto/', views.nuevosalvoconducto, name='nuevosalvoconducto'),
    path('editarsalvoconducto/<int:id>/', views.editarsalvoconducto, name='editarsalvoconducto'),
    path('eliminarsalvoconducto/<int:id>/', views.eliminarsalvoconducto, name='eliminarsalvoconducto'),
    path('salvoconducto/pdf/<int:id>/', views.generar_pdf_salvoconducto, name='pdf_salvoconducto'),
    path('validar/salvoconducto/<int:id>/',views.validar_salvoconducto,name='validar_salvoconducto'),

    #pagos
    path('pago/<int:id_factura>/', views.registrar_pago, name='registrar_pago'),
    path('guardar_pago/', views.guardar_pago, name='guardar_pago'),
    path('pagos/', views.listado_pagos, name='listado_pagos'),
    path('pagos/ver/<int:id_pago>/', views.ver_pago, name='ver_pago'),
    path('pagos/editar/<int:id_pago>/', views.editar_pago, name='editar_pago'),
    path('pagos/eliminar/<int:id_pago>/', views.eliminar_pago, name='eliminar_pago'),



    #pwa
    path("manifest.webmanifest", ManifestView.as_view(), name="manifest"),
    
    path("service-worker.js", ServiceWorkerView.as_view(), name="service-worker"),

    path("offline/", offline, name="offline"),


]

