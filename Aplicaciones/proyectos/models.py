from django.db import models
from django.utils import timezone



class Usuario(models.Model):
    id_usuario=models.AutoField(primary_key=True)
    nombre_usuario=models.CharField(max_length=100)
    apellido_usuario=models.CharField(max_length=100)
    correo_usuario=models.EmailField(unique=True)
    contrasena_usuario = models.CharField(max_length=128)




class Vehiculo(models.Model): 
    id_vehiculo = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="vehiculos")
    tipovehiculo_vehiculo  = models.CharField(max_length=50, choices=[('PRIVADO', 'PRIVADO'), ('TAXI', 'TAXI'), ('MOTOCICLETA', 'MOTOCICLETA'), ('CAMION', 'CAMION')])
    tipocombustible_vehiculo  = models.CharField(max_length=50, choices=[('EXTRA', 'EXTRA'), ('DIESEL', 'DIESEL'), ('SUPER', 'SUPER')])
    matricula_vehiculo  = models.CharField(max_length=100, unique=True)
    modelo_vehiculo  = models.CharField(max_length=50, blank=True)



#punto de inicio
class UbicacionVehiculo(models.Model):
    id_ubicacion=models.AutoField(primary_key=True)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="UbicacionVehiculos")
    latitud = models.FloatField()
    longitud = models.FloatField()
    fecha_hora = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.latitud}, {self.longitud} ({self.fecha_hora})"


#punto 
class Lugarguardado(models.Model):
    id_Lugarguardado=models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="Lugarguardados")
    nombre_Lugarguardado = models.CharField(max_length=900) 
    latitud_Lugarguardado = models.FloatField()
    longitud_Lugarguardado = models.FloatField()
    fecha_guardado = models.DateTimeField(default=timezone.now)

    def __str__(self):
            return f"{self.nombre_Lugarguardado} ({self.latitud_Lugarguardado}, {self.longitud_Lugarguardado})"






class NodoMapa(models.Model):
    id_nodo = models.BigIntegerField(primary_key=True)
    nombre = models.CharField(max_length=200)   # Ej: "Parque La Laguna"
    latitud = models.FloatField()
    longitud = models.FloatField()
    tipo = models.CharField(
        max_length=50,
        choices=[
            ('INTERSECCION', 'Intersección'),
            ('PUNTO_INTERES', 'Punto de interés'),
            ('PARROQUIA', 'Parroquia'),
        ],
        default='INTERSECCION'
    )

    def __str__(self):
        return self.nombre



class TramoVial(models.Model):
    id_tramo = models.AutoField(primary_key=True)
    origen = models.ForeignKey(NodoMapa, on_delete=models.CASCADE, related_name='tramos_salida')
    destino = models.ForeignKey(NodoMapa, on_delete=models.CASCADE, related_name='tramos_llegada')
    distancia_km = models.FloatField()         
    tiempo_base_min = models.FloatField()      
    tipo_via = models.CharField(
        max_length=50,
        choices=[
            ('URBANA', 'Urbana'),
            ('RURAL', 'Rural'),
            ('PRINCIPAL', 'Principal'),
            ('SECUNDARIA', 'Secundaria'),
        ],
        blank=True
    )

    def __str__(self):
        return f"{self.origen} -> {self.destino}"





# me permite guardar en la navegacion origen- destino
class Viaje(models.Model):
    id_viaje = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="viajes")
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="viajes")
    origen = models.ForeignKey(UbicacionVehiculo, on_delete=models.CASCADE)
    destino = models.ForeignKey(Lugarguardado, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Viaje {self.id_viaje} - {self.usuario.nombre_usuario}"






#ruta calculada por cada viaje
class RutaOpcion(models.Model):
    id_ruta_opcion = models.AutoField(primary_key=True)
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name="opciones")
    TIPO_CHOICES = [('OPTIMA', 'Óptima'),('LARGA', 'Larga'),('SEGURA', 'Segura'),]
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    tiempo_min = models.FloatField()
    distancia_km = models.FloatField()
    consumo_litros = models.FloatField(null=True, blank=True)
    costo_estimado = models.FloatField(null=True, blank=True)


    def __str__(self):
        return f"Viaje {self.viaje.id_viaje} "






class PrecioCombustible(models.Model):
    TIPO_CHOICES = [('EXTRA', 'EXTRA'),('DIESEL', 'DIESEL'),('SUPER', 'SUPER'),('ECOPAIS', 'ECOPAIS'),]
    id_precio = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    precio_por_litro = models.FloatField()  

    def __str__(self):
        return f"{self.tipo} - {self.precio_por_litro} USD/L"

