from django.db import models
from django.utils import timezone


class Usuario(models.Model):
    id_usuario=models.AutoField(primary_key=True)
    nombre_usuario=models.CharField(max_length=100)
    apellido_usuario=models.CharField(max_length=100)
    correo_usuario=models.EmailField(unique=True)
    contrasena_usuario = models.CharField(max_length=128)
    tiporol  = models.CharField(max_length=20, choices=[('USUARIO', 'USUARIO'), ('ADMINISTRADOR', 'ADMINISTRADOR')])



class Administrador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)#tabla Administrador con relación OneToOne (1 a 1)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    codigo_interno = models.CharField(max_length=50, unique=True, null=True, blank=True)
    telefono_institucional = models.CharField(max_length=20, null=True, blank=True)



class ChecklistVehiculo(models.Model):
    id_checklist = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="checklists")
    creado_en = models.DateTimeField(default=timezone.now)
    SI_NO = (('SI', 'Si'), ('NO', 'No'))
    # Documentos indispensables
    licencia_conducir = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    tarjeta_circulacion = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    poliza_impresa = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    poliza_digital = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    verificacion_vehicular = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    factura_propiedad = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)

    # Chequeo mecánico esencial
    llantas = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    frenos = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    luces = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    fluidos_aceite = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    fluido_agua = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    bateria_general = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    cinturones = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    limpiaparabrisas = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)

    # Estado general del motor
    motor_aceite = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    motor_refrigerante = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    motor_temperatura = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    motor_bateria = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    motor_filtro_aire = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    motor_fugas = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    motor_combustible = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)

    # Suspensión / transmisión
    amortiguadores = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    alineacion = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    soportes_motor = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    caja = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    embrague = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)

    # Equipo de seguridad requerido
    triangulo = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    chaleco = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    extintor = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    gato_llave = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    botiquin = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    linterna = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    cables_corriente = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    tacos_ruedas = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)
    llanta_reparacion = models.CharField(max_length=2, choices=SI_NO, null=True, blank=True)

    def __str__(self):
        return f"Checklist #{self.id_checklist} - {self.usuario.nombre_usuario} ({self.creado_en.date()})"



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


#punto final
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
    nombre = models.CharField(max_length=200)  
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
    tipo_via = models.CharField(max_length=50,choices=[('URBANA', 'Urbana'),('RURAL', 'Rural'),('PRINCIPAL', 'Principal'),('SECUNDARIA', 'Secundaria'),],blank=True)

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
    tipo  = models.CharField(max_length=20, choices=[('OPTIMA', 'OPTIMA'), ('LARGA', 'LARGA'), ('SEGURA', 'SEGURA')])
    tiempo_min = models.FloatField()
    distancia_km = models.FloatField()
    consumo_litros = models.FloatField(null=True, blank=True)
    costo_estimado = models.FloatField(null=True, blank=True)
    combustible_tipo = models.CharField(max_length=20,choices=[('EXTRA', 'EXTRA'), ('DIESEL', 'DIESEL'),('SUPER', 'SUPER'), ('ECOPAIS', 'ECOPAIS')],null=True,blank=True)


    class Meta:#Evitar duplicados en RutaOpcion
        constraints = [
            models.UniqueConstraint(fields=["viaje", "tipo"], name="uniq_viaje_tipo")
        ]


    def __str__(self):
        return f"Viaje {self.viaje.id_viaje} "



class EventoAdmin(models.Model):
    id_evento = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=200)
    inicio_fecha = models.DateField()
    inicio_hora = models.TimeField()
    fin_fecha = models.DateField(null=True, blank=True)
    fin_hora = models.TimeField(null=True, blank=True)
    descripcion = models.TextField(blank=True)
    creado_por = models.ForeignKey('Administrador', on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.titulo} ({self.inicio_fecha} {self.inicio_hora})"




class AsignacionEvento(models.Model):
    id_usuario_evento = models.AutoField(primary_key=True)
    descripcion_evento = models.TextField(blank=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    evento = models.ForeignKey(EventoAdmin, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(null=True, blank=True)
    ESTADOS = (('PENDIENTE', 'PENDIENTE'),('COMPLETADO', 'COMPLETADO'),('ATRASADO', 'ATRASADO'),('NO COMPLETADO', 'NO COMPLETADO'),)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    estado_fecha = models.DateTimeField(null=True, blank=True)  # cuándo cambió el estado

    class Meta:
        unique_together = ('usuario', 'evento')

    def __str__(self):
        return f"{self.usuario.nombre_usuario} asignado a {self.evento.titulo}"






class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nombre_proveedor = models.CharField(max_length=150)
    direccion_proveedor = models.CharField(max_length=255, blank=True, null=True)
    telefono_proveedor = models.CharField(max_length=20, blank=True, null=True)
    correo_proveedor = models.EmailField(unique=True)
    ruc_proveedor = models.CharField(max_length=13, unique=True)
    estado_proveedor = models.CharField(max_length=20, choices=[('ACTIVO', 'ACTIVO'),('INACTIVO', 'INACTIVO')])






class Pedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    descripcion_pedido = models.TextField(blank=True, null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    evento = models.ForeignKey(EventoAdmin, on_delete=models.SET_NULL, null=True, blank=True)  # Viaje
    fecha_pedido = models.DateField()
    estado_pedido = models.CharField(max_length=20, choices=[('PENDIENTE', 'PENDIENTE'),('EN PROCESO', 'EN PROCESO'),('ENTREGADO', 'ENTREGADO'),('CANCELADO', 'CANCELADO')])



   

class DetallePedido(models.Model):
    id_detalle_pedido = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(Pedido,on_delete=models.CASCADE)
    descripcion_item = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10,decimal_places=2,default=0)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.descripcion_item} - Pedido #{self.pedido.id_pedido}"








#tablas con valores extra unicas


class PrecioCombustible(models.Model):
    TIPO_CHOICES = [('EXTRA', 'EXTRA'),('DIESEL', 'DIESEL'),('SUPER', 'SUPER'),('ECOPAIS', 'ECOPAIS'),]
    id_precio = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    precio_por_litro = models.FloatField()  

    def __str__(self):
        return f"{self.tipo} - {self.precio_por_litro} USD/L"



class RendimientoVehiculoTipo(models.Model):
    tipo  = models.CharField(max_length=20, choices=[('PRIVADO', 'PRIVADO'), ('TAXI', 'TAXI'), ('MOTOCICLETA', 'MOTOCICLETA'), ('CAMION', 'CAMION')])
    # km por litro en contexto urbano / carretera
    km_l_ciudad = models.FloatField()
    km_l_carretera = models.FloatField()

    # litros por hora en ralentí (motor encendido sin avanzar / stop&go)
    idle_l_h = models.FloatField(default=0.8)

    def __str__(self):
        return f"{self.tipo} (ciudad {self.km_l_ciudad} km/L, carretera {self.km_l_carretera} km/L, idle {self.idle_l_h} L/h)"


