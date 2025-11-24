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



class UbicacionVehiculo(models.Model):
    id_ubicacion=models.AutoField(primary_key=True)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="UbicacionVehiculos")
    latitud = models.FloatField()
    longitud = models.FloatField()
    fecha_hora = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.latitud}, {self.longitud} ({self.fecha_hora})"



class Lugarguardado(models.Model):
    id_Lugarguardado=models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="Lugarguardados")
    nombre_Lugarguardado = models.CharField(max_length=100) 
    latitud_Lugarguardado = models.FloatField()
    longitud_Lugarguardado = models.FloatField()
    fecha_guardado = models.DateTimeField(default=timezone.now)

    def __str__(self):
            return f"{self.nombre_Lugarguardado} ({self.latitud_Lugarguardado}, {self.longitud_Lugarguardado})"





