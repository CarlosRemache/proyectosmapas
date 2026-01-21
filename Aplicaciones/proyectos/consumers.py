import json 
from channels.generic.websocket import AsyncWebsocketConsumer 
from .models import UbicacionVehiculo 
from asgiref.sync import sync_to_async 



class UbicacionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("vehiculos", self.channel_name)
        await self.accept()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("vehiculos", self.channel_name)



    async def receive(self, text_data):
        data = json.loads(text_data)
        lat = data['latitud']
        lon = data['longitud']
        vehiculo_id = data.get("vehiculo_id")
        client_id = data.get("client_id")   #nuevo

        # Guardar SIEMPRE (si viene vehiculo_id)
        if vehiculo_id:
            await sync_to_async(UbicacionVehiculo.objects.create)(
                vehiculo_id=vehiculo_id,
                latitud=lat,
                longitud=lon
            )

        await self.channel_layer.group_send(
            "vehiculos",
            {
                "type": "nueva_ubicacion",
                "latitud": lat,
                "longitud": lon,
                "client_id": client_id, #nuevo
            }
        )

    
    async def nueva_ubicacion(self, event):
        await self.send(text_data=json.dumps({
            "latitud": event["latitud"],
            "longitud": event["longitud"],
            "client_id": event.get("client_id"),#nuevo
        }))


