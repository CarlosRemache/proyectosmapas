import json
from channels.generic.websocket import AsyncWebsocketConsumer

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

        # Enviar a todos los clientes conectados
        await self.channel_layer.group_send(
            "vehiculos",
            {
                "type": "nueva_ubicacion",
                "latitud": lat,
                "longitud": lon,
            }
        )

    async def nueva_ubicacion(self, event):
        await self.send(text_data=json.dumps({
            "latitud": event["latitud"],
            "longitud": event["longitud"],
        }))
