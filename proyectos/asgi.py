import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import Aplicaciones.proyectos.routing  

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectos.settings')
django.setup()

# Configura la aplicación ASGI
application = ProtocolTypeRouter({
    # Maneja solicitudes HTTP normales
    "http": get_asgi_application(),

    # Maneja conexiones WebSocket
    "websocket": AuthMiddlewareStack(
        URLRouter(
            Aplicaciones.proyectos.routing.websocket_urlpatterns
        )
    ),
})
