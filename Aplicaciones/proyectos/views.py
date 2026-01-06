from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario, Vehiculo, Lugarguardado, UbicacionVehiculo, PrecioCombustible,NodoMapa,Viaje,RutaOpcion,EventoAdmin,Administrador,AsignacionEvento,Proveedor,Pedido,DetallePedido,ChecklistVehiculo,Pago,Salvoconducto,Factura
from Aplicaciones.proyectos.rutas_utils import (construir_grafo,dijkstra,calcular_metricas_ruta,nodo_mas_cercano,nodos_mas_cercanos,calcular_ruta_larga,construir_grafo_seguro,calcular_ruta_segura)
from django.utils.dateparse import parse_date, parse_time
from django.views.decorators.http import require_GET
from django.db.models.functions import TruncMonth
from django.db.models.functions import Round
from datetime import datetime,timedelta
from django.core.mail import send_mail
from django.utils.timezone import now
from django.db.models import Sum,Count
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
import json
import requests
import random



def login_usuario(request):
    if request.session.get('usuario_id'):
        if request.session.get('usuario_tiporol') == 'ADMINISTRADOR':
            return redirect('/adminpanel/')
        return redirect('/inicio')

    if request.method == 'POST':
        usuario_in = request.POST.get('usuario', '').strip()
        contrasena = request.POST.get('contrasena', '').strip()
        rol_elegido = request.POST.get('rol', '').strip()

        if not rol_elegido:
            messages.error(request, "Debes seleccionar un rol.")
            return render(request, 'login.html')

        try:
            usuario = Usuario.objects.get(
                correo_usuario=usuario_in,
                contrasena_usuario=contrasena
            )
            # validar que el rol coincida con el del usuario
            if usuario.tiporol != rol_elegido:
                messages.error(request, "Rol incorrecto para este usuario.")
                return render(request, 'login.html')
            
            # si elige ADMINISTRADOR, debe existir en tabla Administrador
            if rol_elegido == "ADMINISTRADOR":
                try:
                    admin = Administrador.objects.get(usuario=usuario)
                except Administrador.DoesNotExist:
                    messages.error(request, "Este usuario NO tiene perfil de administrador.")
                    return render(request, 'login.html')

            # Guardar sesión
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_nombre'] = usuario.nombre_usuario
            request.session['usuario_apellido'] = usuario.apellido_usuario
            request.session['usuario_tiporol'] = usuario.tiporol

            messages.success(request, "Inicio de sesión exitoso")

            if rol_elegido == 'ADMINISTRADOR':
                return redirect('/adminpanel/')

            return redirect('/inicio')

        except Usuario.DoesNotExist:
            messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, 'login.html')




def admin_panel(request):
    if not request.session.get('usuario_id'):
        return redirect('/login')

    if request.session.get('usuario_tiporol') != 'ADMINISTRADOR':
        messages.error(request, "No tienes permisos para acceder.")
        return redirect('/inicio')
    return render(request, "administrador/admin_panel.html")



#sirve para cerrar la cesion 
def logout_usuario(request):
    request.session.flush()
    messages.success(request, "Sesión cerrada correctamente")
    return redirect('/login') #devuelve la pantalla en login




def inicio(request):
    # Proteger el inicio: solo usuarios logueados
    if not request.session.get('usuario_id'):
        return redirect('/login')
    
    usuario_id = request.session.get('usuario_id')
    vehiculo = Vehiculo.objects.filter(usuario_id=usuario_id).first()
    return render(request, 'inicio.html', {'vehiculo': vehiculo})



def nuevousuario(request):
    return render(request, 'nuevousuario.html')


def guardarusuario(request):
    if request.method == 'POST':
        nombre_usuario = request.POST['txt_nombre']
        apellido_usuario = request.POST['txt_apellido']
        correo_usuario = request.POST['txt_correo']
        contrasena_usuario = request.POST['txt_contrasena']

        # Generar código de 4 dígitos
        codigo = str(random.randint(1000, 9999))

        # Guardar los datos del registro y el código en la sesión
        request.session['registro_usuario'] = {
            'nombre': nombre_usuario,
            'apellido': apellido_usuario,
            'correo': correo_usuario,
            'contrasena': contrasena_usuario,
            'codigo': codigo,
        }

        # Enviar el correo con el código
        try:
            send_mail(
                'Código de verificación',
                f'Tu código de verificación es: {codigo}',
                'carlos.remache5649@utc.edu.ec',  # remitente (EMAIL_HOST_USER)
                [correo_usuario],                  # destinatario: el correo que ingresó el usuario
                fail_silently=False,
            )
        except Exception as e:
            messages.error(request, f"No se pudo enviar el correo: {e}")
            return redirect('/nuevousuario/')

        # 4) Avisar y redirigir a la página donde se ingresa el código
        messages.success(request, "Te hemos enviado un código de verificación a tu correo. Revísalo e ingrésalo.")
        return redirect('/verificar_registro/')
    return redirect('/nuevousuario/')



def editarusuario(request, id):
    usuario = Usuario.objects.get(id_usuario=id)
    return render(request, 'editarusuario.html', {'usuario': usuario})





def procesareditarusuario(request):
    usuario = Usuario.objects.get(id_usuario=request.POST['id_usuario'])
    usuario.nombre_usuario = request.POST['txt_nombre']
    usuario.apellido_usuario = request.POST['txt_apellido']
    usuario.correo_usuario = request.POST['txt_correo']

    nueva_contra = request.POST['txt_contrasena']
    if nueva_contra != "":
        usuario.contrasena_usuario = nueva_contra
        
    usuario.save()

    messages.success(request, "Usuario actualizado correctamente")
    return redirect('/perfilusuario/')



def listadousuario(request):
    usuarios = Usuario.objects.all()
    # Conteos por rol
    total_usuarios = Usuario.objects.filter(tiporol='USUARIO').count()
    total_admins = Usuario.objects.filter(tiporol='ADMINISTRADOR').count()

    return render(request, 'administrador/listadousuario.html', {
        'usuarios': usuarios,
        'total_usuarios': total_usuarios,
        'total_admins': total_admins
    })






def perfilusuario(request):
    usuario_id = request.session.get('usuario_id') #obtiene el id del usuario creado
    usuario = Usuario.objects.get(id_usuario=usuario_id) #busca el usuario en la base de datos
    return render(request, 'perfilusuario.html', {'usuario': usuario})


def verificar_registro(request):
    # Leer datos guardados en la sesión
    datos = request.session.get('registro_usuario')
    if not datos:
        messages.error(request, "No hay datos de registro pendientes. Intenta nuevamente.")
        return redirect('/nuevousuario/')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '').strip()

        # Comparar código
        if codigo_ingresado == datos['codigo']:
            # Verificar que no exista ya un usuario con ese correo
            if Usuario.objects.filter(correo_usuario=datos['correo']).exists():
                messages.error(request, "Ya existe un usuario con ese correo.")
                # limpiamos sesión para que no se quede basura
                del request.session['registro_usuario']
                return redirect('/login')

            # Crear el usuario
            nuevousuario = Usuario.objects.create(
                nombre_usuario=datos['nombre'],
                apellido_usuario=datos['apellido'],
                correo_usuario=datos['correo'],
                contrasena_usuario=datos['contrasena'],
                tiporol='USUARIO'
            )

            # Limpiar los datos de la sesión
            del request.session['registro_usuario']

            messages.success(request, "Usuario creado correctamente. Ahora puedes iniciar sesión.")
            return redirect('/login')
        else:
            messages.error(request, "Código incorrecto, inténtalo nuevamente.")
    #mostrar formulario para ingresar el código
    return render(request, 'verificar_registro.html')

#documento---------------------------------------------------------------------------------------------------

def creardocumento(request):
    id_usuario = request.session.get('usuario_id')
    if not id_usuario:
        return redirect('/login/')  

    usuario = Usuario.objects.get(id_usuario=id_usuario)

    checklist = ChecklistVehiculo.objects.filter(
        usuario=usuario
    ).order_by('-creado_en').first()

    if checklist:
        edit_mode = 'edit' in request.GET
    else:
        edit_mode = True  

    if request.method == 'POST':
        data = request.POST

        if checklist:
            c = checklist
            c.licencia_conducir = data.get('licencia_conducir')
            c.tarjeta_circulacion = data.get('tarjeta_circulacion')
            c.poliza_impresa = data.get('poliza_impresa')
            c.poliza_digital = data.get('poliza_digital')
            c.verificacion_vehicular = data.get('verificacion_vehicular')
            c.factura_propiedad = data.get('factura_propiedad')

            # Chequeo mecánico
            c.llantas = data.get('llantas')
            c.frenos = data.get('frenos')
            c.luces = data.get('luces')
            c.fluidos_aceite = data.get('fluidos_aceite')
            c.fluido_agua = data.get('fluido_agua')
            c.bateria_general = data.get('bateria_general')
            c.cinturones = data.get('cinturones')
            c.limpiaparabrisas = data.get('limpiaparabrisas')

            # Motor
            c.motor_aceite = data.get('motor_aceite')
            c.motor_refrigerante = data.get('motor_refrigerante')
            c.motor_temperatura = data.get('motor_temperatura')
            c.motor_bateria = data.get('motor_bateria')
            c.motor_filtro_aire = data.get('motor_filtro_aire')
            c.motor_fugas = data.get('motor_fugas')
            c.motor_combustible = data.get('motor_combustible')

            # Suspensión / transmisión
            c.amortiguadores = data.get('amortiguadores')
            c.alineacion = data.get('alineacion')
            c.soportes_motor = data.get('soportes_motor')
            c.caja = data.get('caja')
            c.embrague = data.get('embrague')

            # Equipo de seguridad
            c.triangulo = data.get('triangulo')
            c.chaleco = data.get('chaleco')
            c.extintor = data.get('extintor')
            c.gato_llave = data.get('gato_llave')
            c.botiquin = data.get('botiquin')
            c.linterna = data.get('linterna')
            c.cables_corriente = data.get('cables_corriente')
            c.tacos_ruedas = data.get('tacos_ruedas')
            c.llanta_reparacion = data.get('llanta_reparacion')

            c.save()
            messages.success(request, "Checklist actualizado correctamente.")
        else:
            # CREAR nuevo checklist
            checklist = ChecklistVehiculo.objects.create(
                usuario=usuario,

                # Documentos indispensables
                licencia_conducir=data.get('licencia_conducir'),
                tarjeta_circulacion=data.get('tarjeta_circulacion'),
                poliza_impresa=data.get('poliza_impresa'),
                poliza_digital=data.get('poliza_digital'),
                verificacion_vehicular=data.get('verificacion_vehicular'),
                factura_propiedad=data.get('factura_propiedad'),

                # Chequeo mecánico
                llantas=data.get('llantas'),
                frenos=data.get('frenos'),
                luces=data.get('luces'),
                fluidos_aceite=data.get('fluidos_aceite'),
                fluido_agua=data.get('fluido_agua'),
                bateria_general=data.get('bateria_general'),
                cinturones=data.get('cinturones'),
                limpiaparabrisas=data.get('limpiaparabrisas'),

                # Motor
                motor_aceite=data.get('motor_aceite'),
                motor_refrigerante=data.get('motor_refrigerante'),
                motor_temperatura=data.get('motor_temperatura'),
                motor_bateria=data.get('motor_bateria'),
                motor_filtro_aire=data.get('motor_filtro_aire'),
                motor_fugas=data.get('motor_fugas'),
                motor_combustible=data.get('motor_combustible'),

                # Suspensión / transmisión
                amortiguadores=data.get('amortiguadores'),
                alineacion=data.get('alineacion'),
                soportes_motor=data.get('soportes_motor'),
                caja=data.get('caja'),
                embrague=data.get('embrague'),

                # Equipo de seguridad
                triangulo=data.get('triangulo'),
                chaleco=data.get('chaleco'),
                extintor=data.get('extintor'),
                gato_llave=data.get('gato_llave'),
                botiquin=data.get('botiquin'),
                linterna=data.get('linterna'),
                cables_corriente=data.get('cables_corriente'),
                tacos_ruedas=data.get('tacos_ruedas'),
                llanta_reparacion=data.get('llanta_reparacion'),
            )
            messages.success(request, "Checklist guardado correctamente.")

        # Después de guardar, volvemos en modo lectura
        return redirect('creardocumento')
    bloqueado = bool(checklist) and not edit_mode

    return render(request, 'creardocumento.html', {
        'usuario': usuario,
        'checklist': checklist,
        'bloqueado': bloqueado,
        'edit_mode': edit_mode,
    })



# Vehiculo-------------------------------------------------------------

def nuevovehiculo(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        messages.error(request, "Inicia sesión nuevamente.")
        return redirect('/login')

    usuario = Usuario.objects.filter(id_usuario=usuario_id).first()
    if not usuario:
        request.session.flush()
        messages.error(request, "Tu sesión no es válida. Inicia sesión nuevamente.")
        return redirect('/login')

    tiene_vehiculo = Vehiculo.objects.filter(usuario=usuario).exists()
    return render(request, 'nuevovehiculo.html', {'usuario': usuario, 'tiene_vehiculo': tiene_vehiculo})



def guardarvehiculo(request):
    id_usuario = request.POST['usuario']
    tipovehi = request.POST['txt_tipo_vehiculo']
    tipocomb = request.POST['txt_tipo_combustible']
    matricula = request.POST['txt_matricula']
    modelo = request.POST['txt_modelo']
    usuario = Usuario.objects.get(id_usuario=id_usuario)
    Vehiculo.objects.create(
        usuario=usuario,
        tipovehiculo_vehiculo=tipovehi,
        tipocombustible_vehiculo=tipocomb,
        matricula_vehiculo=matricula,
        modelo_vehiculo=modelo
    )

    messages.success(request, "Vehículo guardado")
    return redirect('/listadovehiculo')



def listadovehiculo(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        messages.error(request, "Inicia sesión nuevamente.")
        return redirect('/login')

    usuario = Usuario.objects.filter(id_usuario=usuario_id).first()
    if not usuario:
        request.session.flush()
        messages.error(request, "Tu sesión no es válida. Inicia sesión nuevamente.")
        return redirect('/login')

    vehiculo = Vehiculo.objects.filter(usuario=usuario).first()
    return render(request, 'listadovehiculo.html', {'vehiculo': vehiculo})



def eliminarvehiculo(request, id):
    vehiculo = Vehiculo.objects.get(id_vehiculo=id)
    vehiculo.delete()
    messages.success(request, "Vehículo eliminado")
    return redirect('/inicio')


def editarvehiculo(request, id):
    id_usuario = request.session.get('usuario_id') 
    vehiculo = Vehiculo.objects.get(id_vehiculo=id)
    usuarios = Usuario.objects.get(id_usuario=id_usuario)
    return render(request, 'editarvehiculo.html', {'vehiculo': vehiculo, 'usuarios': usuarios})


def procesareditarvehiculo(request):
    vehiculo = Vehiculo.objects.get(id_vehiculo=request.POST['id'])
    vehiculo.usuario = Usuario.objects.get(id_usuario=request.POST['usuario'])
    vehiculo.tipovehiculo_vehiculo = request.POST['txt_tipo_vehiculo']
    vehiculo.tipocombustible_vehiculo = request.POST['txt_tipo_combustible']
    vehiculo.matricula_vehiculo = request.POST['txt_matricula']
    vehiculo.modelo_vehiculo = request.POST['txt_modelo']
    vehiculo.save()

    messages.success(request, "Vehículo editado exitosamente")
    return redirect('/listadovehiculo')




#busca en el mapa-------------------------------------------------------------------------------------


def buscarlugares(request):
    query = request.GET.get("q", "") 

    resultados = []
    usuario_id = request.session.get("usuario_id")
    if usuario_id is None:
        messages.error(request, "Debes iniciar sesión")
        return redirect("login")

    historial = Lugarguardado.objects.filter(usuario=usuario_id).order_by('-fecha_guardado')
    
    if query:
        url = "https://nominatim.openstreetmap.org/search" 
        params = {
            "q": query, #El texto que el usuario buscó
            "format": "json", #La respuesta vendrá en formato JSON
            "addressdetails": 1, #Devuelve datos completos como barrio, ciudad, etc.
            "limit": 15, #Máximo 15 resultados
            "viewbox": "-78.7000,-0.8000,-78.5000,-1.0500",  # OESTE,NORTE,ESTE,SUR   ,  Caja rectangular que cubre solo Latacunga
            "bounded": 1,  #  Obligatorio para restringir área,  Obliga que los resultados estén dentro de esa caja
        }

        r = requests.get(url, params=params, headers={"User-Agent": "tuapp"})
        resultados = r.json()

    return render(request, "buscarlugares.html", {
        "query": query,
        "resultados": resultados,
        "historial": historial,
    })


def ver_lugar(request, lat, lon):
    nombre = request.GET.get("nombre", "Ubicación seleccionada")
    return render(request, "ver_lugar.html", {
        "lat": lat,
        "lon": lon,
        "nombre": nombre
    })




def guardar_lugar(request, lat, lon, nombre):
    # Obtener al usuario logueado
    usuario_id = request.session.get("usuario_id")
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    # Guardar en la tabla existente
    Lugarguardado.objects.create(
        usuario=usuario,
        nombre_Lugarguardado=nombre,
        latitud_Lugarguardado=float(lat),
        longitud_Lugarguardado=float(lon)
    )
    messages.success(request, "Lugar guardado con exito")

    return redirect("ver_lugar", lat=lat, lon=lon)





def eliminar_lugar(request, id):
    usuario_id = request.session.get("usuario_id")
    lugar = Lugarguardado.objects.filter(
        id_Lugarguardado=id,  
        usuario_id=usuario_id  
    ).first()

    if not lugar:
        messages.error(
            request,
            "El lugar que intentas eliminar ya no existe o no te pertenece."
        )
        return redirect("buscarlugares")

    lugar.delete()
    messages.success(request, "Lugar eliminado correctamente.")
    return redirect("buscarlugares")


#rutas ----------------------------------------------------------------------------------------------------------------------------

UMBRAL_DISTANCIA_REL = 0.10   # 10% más distancia
UMBRAL_DISTANCIA_ABS = 0.3    # o al menos 0.3 km más
UMBRAL_TIEMPO_REL = 0.10      # 10% más tiempo
UMBRAL_TIEMPO_ABS = 1.0       # o al menos 1 minuto más

def es_significativamente_mas_larga(dist_opt, t_opt, dist_larga, t_larga):
    """
    Devuelve True si la ruta larga es suficientemente más larga
    que la óptima (en distancia o en tiempo).
    """
    # Diferencias
    delta_dist = dist_larga - dist_opt
    delta_t    = t_larga - t_opt

    dist_ok = delta_dist >= max(UMBRAL_DISTANCIA_ABS, dist_opt * UMBRAL_DISTANCIA_REL)
    tiempo_ok = delta_t >= max(UMBRAL_TIEMPO_ABS, t_opt * UMBRAL_TIEMPO_REL)

    return dist_ok or tiempo_ok


# Rendimientos aproximados (km por litro) por tipo de vehículo
RENDIMIENTOS_KM_LITRO = {
    "PRIVADO": 12.0,
    "TAXI": 11.0,
    "MOTOCICLETA": 30.0,
    "CAMION": 5.0,
}


def rutas(request):
    usuario_id = request.session.get("usuario_id")

    lat_get = request.GET.get("lat")
    lon_get = request.GET.get("lon")

    if lat_get and lon_get:
        lat_origen = float(lat_get)
        lon_origen = float(lon_get)
    else:
        origen_obj = UbicacionVehiculo.objects.filter(
            vehiculo__usuario__id_usuario=usuario_id
        ).order_by('-fecha_hora').first()

        if not origen_obj:
            messages.error(request, "No se encontró la ubicación del vehículo.")
            return redirect('/inicio')

        lat_origen = origen_obj.latitud
        lon_origen = origen_obj.longitud


    if not origen_obj:
        messages.error(request, "No se encontró la ubicación del vehículo.")
        return redirect('/inicio')

    lat_origen = origen_obj.latitud
    lon_origen = origen_obj.longitud
    destino_obj = Lugarguardado.objects.filter(usuario_id=usuario_id).last()

    if not destino_obj:
        messages.error(request, "Debes guardar un lugar primero.")
        return redirect('/buscarlugares')

    lat_dest = destino_obj.latitud_Lugarguardado
    lon_dest = destino_obj.longitud_Lugarguardado


    nodo_origen = nodo_mas_cercano(lat_origen, lon_origen)
    nodo_destino = nodo_mas_cercano(lat_dest, lon_dest)

    if not nodo_origen or not nodo_destino:
        messages.error(request, "No se encontraron nodos cercanos en la red vial.")
        return redirect('/inicio')

    grafo = construir_grafo()
    ruta_optima_ids, costo_min = dijkstra(grafo, nodo_origen.id_nodo, nodo_destino.id_nodo)

    # ========= Fallback: probar con varios nodos cercanos si no hay ruta =========
    if not ruta_optima_ids:
        origen_candidatos = nodos_mas_cercanos(lat_origen, lon_origen, k=5)
        destino_candidatos = nodos_mas_cercanos(lat_dest, lon_dest, k=5)

        mejor = None

        for o in origen_candidatos:
            for d in destino_candidatos:
                ruta_tmp, costo_tmp = dijkstra(grafo, o.id_nodo, d.id_nodo)
                if ruta_tmp:
                    mejor = (o, d, ruta_tmp, costo_tmp)
                    break
            if mejor:
                break

        if not mejor:
            messages.error(request, "No se pudo calcular una ruta óptima en la red vial.")
            return redirect('/inicio')

        # Usamos el mejor par encontrado
        nodo_origen, nodo_destino, ruta_optima_ids, costo_min = mejor


    distancia_km_opt, tiempo_min_opt = calcular_metricas_ruta(ruta_optima_ids)


    ruta_larga_ids, costo_largo = calcular_ruta_larga(
        grafo,
        ruta_optima_ids,
        nodo_origen.id_nodo,
        nodo_destino.id_nodo
    )

    distancia_km_larga = None
    tiempo_min_larga = None

    if ruta_larga_ids:
        distancia_km_larga, tiempo_min_larga = calcular_metricas_ruta(ruta_larga_ids)

    ruta_segura_ids = None
    distancia_km_segura = None
    tiempo_min_segura = None

    grafo_seguro = construir_grafo_seguro()

    ruta_segura_ids, costo_seguro = calcular_ruta_segura(
        grafo_seguro,
        ruta_optima_ids,
        ruta_larga_ids,
        nodo_origen.id_nodo,
        nodo_destino.id_nodo
    )

    if ruta_segura_ids:
        distancia_km_segura, tiempo_min_segura = calcular_metricas_ruta(ruta_segura_ids)


    vehiculo = Vehiculo.objects.filter(usuario_id=usuario_id).first()

    if not vehiculo:
        messages.error(request, "Debes registrar un vehículo antes de calcular la ruta.")
        return redirect('/inicio')  

    rendimiento_km_litro = RENDIMIENTOS_KM_LITRO.get(
        vehiculo.tipovehiculo_vehiculo
    )

    precio_obj = PrecioCombustible.objects.filter(
        tipo=vehiculo.tipocombustible_vehiculo
    ).first()

    consumo_opt = costo_opt = None
    consumo_larga = costo_larga = None
    consumo_segura = costo_segura_monto = None 

    if rendimiento_km_litro and precio_obj:
        precio_litro = precio_obj.precio_por_litro


        consumo_opt = distancia_km_opt / rendimiento_km_litro
        costo_opt = consumo_opt * precio_litro


        if distancia_km_larga is not None:
            consumo_larga = distancia_km_larga / rendimiento_km_litro
            costo_larga = consumo_larga * precio_litro


        if distancia_km_segura is not None:
            consumo_segura = distancia_km_segura / rendimiento_km_litro
            costo_segura_monto = consumo_segura * precio_litro


    viaje = Viaje.objects.create(
        usuario_id=usuario_id,
        vehiculo=vehiculo,
        origen=origen_obj,
        destino=destino_obj,
    )

    request.session['viaje_id'] = viaje.id_viaje

    detalles_rutas = []

    # Ruta Óptima
    detalles_rutas.append({
        "distancia_km": distancia_km_opt,
        "tiempo_min": tiempo_min_opt,
        "tipo": "optima",
        "consumo_litros": consumo_opt,
        "costo_ruta": costo_opt,
    })

    # Ruta Larga (solo si realmente existe)
    if ruta_larga_ids and distancia_km_larga and tiempo_min_larga:
        detalles_rutas.append({
            "distancia_km": distancia_km_larga,
            "tiempo_min": tiempo_min_larga,
            "tipo": "larga",
            "consumo_litros": consumo_larga,
            "costo_ruta": costo_larga,
        })

    # Ruta Segura (solo si realmente existe y es distinta)
    if ruta_segura_ids and distancia_km_segura and tiempo_min_segura:
        detalles_rutas.append({
            "distancia_km": distancia_km_segura,
            "tiempo_min": tiempo_min_segura,
            "tipo": "segura",
            "consumo_litros": consumo_segura,
            "costo_ruta": costo_segura_monto,
        })


    todos_ids = set(ruta_optima_ids)
    if ruta_larga_ids:
        todos_ids.update(ruta_larga_ids)
    if ruta_segura_ids:
        todos_ids.update(ruta_segura_ids)

    nodos_dict = NodoMapa.objects.in_bulk(todos_ids, field_name='id_nodo')

    # Ruta Óptima
    coords_ruta_optima = []
    for nid in ruta_optima_ids:
        nodo = nodos_dict.get(nid)
        if nodo:
            coords_ruta_optima.append([nodo.latitud, nodo.longitud])

    rutas_js = [coords_ruta_optima]

    # Ruta Larga
    if ruta_larga_ids:
        coords_ruta_larga = []
        for nid in ruta_larga_ids:
            nodo = nodos_dict.get(nid)
            if nodo:
                coords_ruta_larga.append([nodo.latitud, nodo.longitud])

        if coords_ruta_larga:
            rutas_js.append(coords_ruta_larga)

    # Ruta Segura
    if ruta_segura_ids:
        coords_ruta_segura = []
        for nid in ruta_segura_ids:
            nodo = nodos_dict.get(nid)
            if nodo:
                coords_ruta_segura.append([nodo.latitud, nodo.longitud])

        if coords_ruta_segura:
            rutas_js.append(coords_ruta_segura)

    return render(request, "rutas.html", {
        "origen_real": json.dumps({"latitud": lat_origen, "longitud": lon_origen}),
        "destino_real": json.dumps({
            "latitud": lat_dest,
            "longitud": lon_dest,
            "nombre": destino_obj.nombre_Lugarguardado
        }),
        "rutas_js": json.dumps(rutas_js),
        "detalles_rutas": detalles_rutas,
    })


# recorrido-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def recorrido(request):
    usuario_id = request.session.get("usuario_id")
    tipo_solicitado = request.GET.get("ruta", "optima")  


    vehiculo = Vehiculo.objects.filter(usuario_id=usuario_id).first()


    lat_get = request.GET.get("lat")
    lon_get = request.GET.get("lon")

    if lat_get and lon_get:
        lat_origen = float(lat_get)
        lon_origen = float(lon_get)
    else:
        origen_obj = UbicacionVehiculo.objects.filter(
            vehiculo__usuario__id_usuario=usuario_id
        ).order_by('-fecha_hora').first()

        if not origen_obj:
            messages.error(request, "No se encontró la ubicación del vehículo.")
            return redirect('/inicio')

        lat_origen = origen_obj.latitud
        lon_origen = origen_obj.longitud

    destino_obj = Lugarguardado.objects.filter(usuario_id=usuario_id).last()
    if not destino_obj:
        messages.error(request, "Debes guardar un lugar primero.")
        return redirect('/buscarlugares')

    lat_origen = origen_obj.latitud
    lon_origen = origen_obj.longitud
    lat_dest = destino_obj.latitud_Lugarguardado
    lon_dest = destino_obj.longitud_Lugarguardado

    nodo_origen = nodo_mas_cercano(lat_origen, lon_origen)
    nodo_destino = nodo_mas_cercano(lat_dest, lon_dest)

    if not nodo_origen or not nodo_destino:
        messages.error(request, "No se encontraron nodos cercanos en la red vial.")
        return redirect('/inicio')

    # === Ruta óptima ===
    grafo = construir_grafo()
    ruta_optima_ids, _ = dijkstra(grafo, nodo_origen.id_nodo, nodo_destino.id_nodo)

    if not ruta_optima_ids:
        origen_candidatos = nodos_mas_cercanos(lat_origen, lon_origen, k=5)
        destino_candidatos = nodos_mas_cercanos(lat_dest, lon_dest, k=5)
        mejor = None
        for o in origen_candidatos:
            for d in destino_candidatos:
                rtmp, ctmp = dijkstra(grafo, o.id_nodo, d.id_nodo)
                if rtmp:
                    mejor = (o, d, rtmp)
                    break
            if mejor:
                break
        if not mejor:
            messages.error(request, "No se pudo calcular una ruta en la red vial.")
            return redirect('/inicio')
        nodo_origen, nodo_destino, ruta_optima_ids = mejor

    # === Ruta larga ===
    ruta_larga_ids, _ = calcular_ruta_larga(
        grafo,
        ruta_optima_ids,
        nodo_origen.id_nodo,
        nodo_destino.id_nodo
    )

    # === Ruta segura ===
    grafo_seguro = construir_grafo_seguro()
    ruta_segura_ids, _ = calcular_ruta_segura(
        grafo_seguro,
        ruta_optima_ids,
        ruta_larga_ids,
        nodo_origen.id_nodo,
        nodo_destino.id_nodo
    )


    if tipo_solicitado == "larga" and ruta_larga_ids:
        ruta_seleccionada_ids = ruta_larga_ids
        color_ruta = "#ff8800"
        tipo_bd = "LARGA"
    elif tipo_solicitado == "segura" and ruta_segura_ids:
        ruta_seleccionada_ids = ruta_segura_ids
        color_ruta = "#00ff88"
        tipo_bd = "SEGURA"
    else:
        # fallback a óptima
        ruta_seleccionada_ids = ruta_optima_ids
        color_ruta = "#00aaff"
        tipo_bd = "OPTIMA"


    todos_ids = set(ruta_seleccionada_ids)
    nodos_dict = NodoMapa.objects.in_bulk(todos_ids, field_name='id_nodo')

    coords_ruta = []
    for nid in ruta_seleccionada_ids:
        nodo = nodos_dict.get(nid)
        if nodo:
            coords_ruta.append([nodo.latitud, nodo.longitud])

    rutas_js = [coords_ruta]


    distancia_km, tiempo_min = calcular_metricas_ruta(ruta_seleccionada_ids)

    consumo_litros = None
    costo_estimado = None

    if vehiculo:
        rendimiento = RENDIMIENTOS_KM_LITRO.get(vehiculo.tipovehiculo_vehiculo)
        if rendimiento:
            precio_obj = PrecioCombustible.objects.filter(
                tipo=vehiculo.tipocombustible_vehiculo
            ).first()
            if precio_obj:
                consumo_litros = distancia_km / rendimiento
                costo_estimado = consumo_litros * precio_obj.precio_por_litro


    viaje = None
    viaje_id = request.session.get('viaje_id')
    if viaje_id:
        viaje = Viaje.objects.filter(id_viaje=viaje_id).first()

    if not viaje:
        viaje = Viaje.objects.create(
            usuario_id=usuario_id,
            vehiculo=vehiculo,
            origen=origen_obj,
            destino=destino_obj,
        )
        request.session['viaje_id'] = viaje.id_viaje


    RutaOpcion.objects.create(
        viaje=viaje,
        tipo=tipo_bd,             
        tiempo_min=tiempo_min,
        distancia_km=distancia_km,
        consumo_litros=consumo_litros if consumo_litros is not None else 0,
        costo_estimado=costo_estimado if costo_estimado is not None else 0,
        combustible_tipo=vehiculo.tipocombustible_vehiculo if vehiculo else None,

    )

    return render(request, "recorrido.html", {
        "origen_real": json.dumps({"latitud": lat_origen, "longitud": lon_origen}),
        "destino_real": json.dumps({
            "latitud": lat_dest,
            "longitud": lon_dest,
            "nombre": destino_obj.nombre_Lugarguardado
        }),
        "rutas_js": json.dumps(rutas_js),
        "color_ruta": color_ruta,
        "vehiculo": vehiculo,
    })



#historial-----------------------------------------------------------------------------------------------------------------------------------------

def historial(request):
    # Proteger: solo usuarios logueados
    if not request.session.get('usuario_id'):
        return redirect('/login')

    usuario_id = request.session.get('usuario_id')
    rutas = RutaOpcion.objects.filter(viaje__usuario_id=usuario_id).select_related('viaje', 'viaje__vehiculo').order_by('-viaje__fecha_creacion')
    return render(request, 'historial.html', {
        'rutas': rutas,
    })




def eliminar_ruta_historial(request, id_ruta):
    if not request.session.get('usuario_id'):
        return redirect('/login')

    if request.method != 'POST':
        return redirect('historial')

    usuario_id = request.session.get('usuario_id')
    ruta = RutaOpcion.objects.filter(
        id_ruta_opcion=id_ruta,
        viaje__usuario_id=usuario_id
    ).first()

    if not ruta:
        messages.error(request, "La ruta que intentas eliminar no existe o no te pertenece.")
        return redirect('historial')

    ruta.delete()
    messages.success(request, "Ruta eliminada del historial.")
    return redirect('historial')


#api ruta ---------------------------------------------------------------------------------------------------------

@require_GET
def api_ruta_optima(request):
    """
    Endpoint: devuelve la ruta óptima (mínimo tiempo) entre dos nodos.

    Ejemplo de uso:
    /api/ruta-optima/?origen=8520975411&destino=8520975397
    """
    try:
        origen_id = int(request.GET.get("origen"))
        destino_id = int(request.GET.get("destino"))
    except (TypeError, ValueError):
        return JsonResponse(
            {"error": "Parámetros 'origen' y 'destino' son obligatorios y deben ser enteros."},
            status=400,
        )

    # Verificar que existan los nodos
    try:
        NodoMapa.objects.get(pk=origen_id)
        NodoMapa.objects.get(pk=destino_id)
    except NodoMapa.DoesNotExist:
        return JsonResponse(
            {"error": "Alguno de los nodos (origen o destino) no existe."},
            status=404,
        )

    grafo = construir_grafo()
    ruta_ids, costo = dijkstra(grafo, origen_id, destino_id)

    if not ruta_ids:
        return JsonResponse(
            {"error": "No se encontró ruta entre los nodos indicados."},
            status=404,
        )

    distancia_km, tiempo_min = calcular_metricas_ruta(ruta_ids)

    # Convertir ids de nodos a coordenadas [lon, lat] para el mapa
    nodos = NodoMapa.objects.in_bulk(ruta_ids, field_name="id_nodo")
    coordenadas = []
    for nid in ruta_ids:
        nodo = nodos.get(nid)
        if nodo:
            coordenadas.append([nodo.longitud, nodo.latitud])  # formato típico de mapas

    data = {
        "origen": origen_id,
        "destino": destino_id,
        "ruta_optima": {
            "nodos": ruta_ids,
            "coordenadas": coordenadas,
            "distancia_km": distancia_km,
            "tiempo_min": tiempo_min,
        },
    }

    return JsonResponse(data)


#asignacion usuario-----------------------------------------------------------------------------------------------------


def _solo_usuario(request):
    return request.session.get('usuario_tiporol') == 'USUARIO'


def pedidosusuario(request):
    if not _solo_usuario(request):
        messages.error(request, "No tienes permisos.")
        return redirect('/login')

    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('/login')

    asignaciones = (
        AsignacionEvento.objects
        .filter(usuario_id=usuario_id)
        .select_related('evento', 'evento__creado_por', 'evento__creado_por__usuario')
        .order_by('-fecha_asignacion', '-evento__inicio_fecha', '-evento__inicio_hora')
    )

    return render(request, 'pedidosusuario.html', {
        'asignaciones': asignaciones
    })


def usuario_eventos_json(request):
    if not _solo_usuario(request):
        return JsonResponse([], safe=False)

    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse([], safe=False)

    tz = timezone.get_current_timezone()

    asignaciones = (
        AsignacionEvento.objects
        .filter(usuario_id=usuario_id)
        .select_related('evento')
        .order_by('evento__inicio_fecha', 'evento__inicio_hora')
    )

    data = []
    for a in asignaciones:
        e = a.evento
        start_dt = timezone.make_aware(datetime.combine(e.inicio_fecha, e.inicio_hora), tz)
        end_dt = None
        if e.fin_fecha and e.fin_hora:
            end_dt = timezone.make_aware(datetime.combine(e.fin_fecha, e.fin_hora), tz)

        data.append({
            "id": e.id_evento,
            "title": e.titulo,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat() if end_dt else None,
        })

    return JsonResponse(data, safe=False)



def usuario_cambiar_estado(request, asig_id):
    # Cambia el estado: COMPLETADO / ATRASADO / NO_COMPLETADO
    if request.method != "POST":
        return redirect("pedidosusuario") 

    if not _solo_usuario(request):
        messages.error(request, "No tienes permisos.")
        return redirect("/login")

    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        messages.error(request, "Sesión no válida.")
        return redirect("/login")

    nuevo_estado = request.POST.get("estado")
    if nuevo_estado not in ["COMPLETADO", "ATRASADO", "NO_COMPLETADO"]:
        messages.error(request, "Estado inválido.")
        return redirect("pedidosusuario")

    asign = (
        AsignacionEvento.objects
        .select_related("evento")
        .filter(id_usuario_evento=asig_id, usuario_id=usuario_id)
        .first()
    )

    if not asign:
        messages.error(request, "Asignación no encontrada.")
        return redirect("pedidosusuario")

    e = asign.evento

    # Validación: debe existir fin
    if not (e.fin_fecha and e.fin_hora):
        messages.error(request, "Este evento no tiene fecha/hora fin.")
        return redirect("pedidosusuario")

    ahora = timezone.localtime()
    fin_dt = timezone.make_aware(
        datetime.combine(e.fin_fecha, e.fin_hora),
        timezone.get_current_timezone()
    )

    # COMPLETADO: solo cuando ya terminó y dentro de 5 minutos

    if nuevo_estado == "COMPLETADO":

        inicio_dt = timezone.make_aware(
            datetime.combine(e.inicio_fecha, e.inicio_hora),
            timezone.get_current_timezone()
        )

        # Antes del inicio 
        if ahora < inicio_dt:
            messages.error(request, "El evento aún no ha iniciado.")
            return redirect("pedidosusuario")

        # Después de fin + 5 minutos 
        if ahora > fin_dt + timedelta(minutes=5):
            messages.error(
                request,
                "El tiempo para marcar como completado ya terminó (5 minutos después del fin)."
            )
            return redirect("pedidosusuario")




    # ATRASADO / NO_COMPLETADO: solo después de fin
    if nuevo_estado in ["ATRASADO", "NO_COMPLETADO"]:
        if ahora < fin_dt:
            messages.error(request, "Aún no termina el evento.")
            return redirect("pedidosusuario")

    # Guardar en BD (requiere campos estado y estado_fecha en AsignacionEvento)
    asign.estado = nuevo_estado
    asign.estado_fecha = timezone.now()
    asign.save(update_fields=["estado", "estado_fecha"])

    messages.success(request, f"Estado actualizado a: {nuevo_estado}.")
    return redirect("pedidosusuario")







def _solo_admin(request):
    return request.session.get('usuario_tiporol') == 'ADMINISTRADOR'


def reporte_asignaciones(request):
    """
    Vista SOLO ADMIN para ver el estado de las asignaciones
    """
    if not _solo_admin(request):
        messages.error(request, "No tienes permisos.")
        return redirect('/login')

    estado_filtro = request.GET.get("estado")  # COMPLETADO / ATRASADO / NO_COMPLETADO / PENDIENTE
    asignaciones = (
        AsignacionEvento.objects
        .select_related("usuario", "evento", "evento__creado_por", "evento__creado_por__usuario")
        .order_by("-fecha_asignacion", "-evento__inicio_fecha", "-evento__inicio_hora")
    )

    if estado_filtro in ["COMPLETADO", "ATRASADO", "NO_COMPLETADO", "PENDIENTE"]:
        asignaciones = asignaciones.filter(estado=estado_filtro)

    total = AsignacionEvento.objects.count()
    total_completados = AsignacionEvento.objects.filter(estado="COMPLETADO").count()
    total_atrasados = AsignacionEvento.objects.filter(estado="ATRASADO").count()
    total_nocomp = AsignacionEvento.objects.filter(estado="NO_COMPLETADO").count()
    total_pendientes = AsignacionEvento.objects.filter(estado="PENDIENTE").count()

    contexto = {
        "asignaciones": asignaciones,
        "estado_filtro": estado_filtro,
        "total": total,
        "total_completados": total_completados,
        "total_atrasados": total_atrasados,
        "total_nocomp": total_nocomp,
        "total_pendientes": total_pendientes,
    }
    return render(request, "administrador/reporte_asignaciones.html", contexto)




#noticicaciones---------------------------------------------------------------------------------------------------------

def usuario_toast_evento(request):
    id_usuario = request.session.get("usuario_id")
    if not id_usuario:
        return JsonResponse({"ok": False})

    asign = (
        AsignacionEvento.objects
        .filter(usuario_id=id_usuario)
        .select_related("evento")
        .order_by("-fecha_asignacion")
        .first()
    )

    if not asign:
        return JsonResponse({"ok": False})

    e = asign.evento

    inicio_dt = datetime.combine(e.inicio_fecha, e.inicio_hora)
    inicio_txt = inicio_dt.strftime("%d-%m-%Y %I:%M %p")

    #  si no hay fin, puedes decidir: que nunca se detenga, o que no muestre
    if e.fin_fecha and e.fin_hora:
        fin_dt = datetime.combine(e.fin_fecha, e.fin_hora)
        fin_txt = fin_dt.strftime("%d-%m-%Y %I:%M %p")
        fin_iso = fin_dt.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        fin_txt = "Sin final"
        fin_iso = None

    return JsonResponse({
        "ok": True,
        "inicio": inicio_txt,
        "fin": fin_txt,
        "fin_iso": fin_iso,   
        "descripcion": e.descripcion or "-"
    })





#panel de administrador-------------------------------------------------------------------------------------------------------------

#calendario--------------------------------------------------------------------------------------------------

def _solo_admin(request):
    return request.session.get('usuario_tiporol') == 'ADMINISTRADOR'# Solo para administradores



def admin_calendario(request):
    if not _solo_admin(request):
        messages.error(request, "No tienes permisos.")
        return redirect('/login')
    return render(request, 'administrador/admin_calendario.html')


def admin_eventos_json(request):
    if not _solo_admin(request):
        return JsonResponse([], safe=False)

    eventos = EventoAdmin.objects.all().order_by('inicio_fecha', 'inicio_hora')
    tz = timezone.get_current_timezone()

    data = []
    for e in eventos:
        start_dt = timezone.make_aware(datetime.combine(e.inicio_fecha, e.inicio_hora), tz)

        end_dt = None
        if e.fin_fecha and e.fin_hora:
            end_dt = timezone.make_aware(datetime.combine(e.fin_fecha, e.fin_hora), tz)

        data.append({
            "id": e.id_evento,
            "title": e.titulo,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat() if end_dt else None,
        })

    return JsonResponse(data, safe=False)



def admin_evento_crear(request):# Crear evento
    if not _solo_admin(request):
        messages.error(request, "No tienes permisos.")
        return redirect('/login')

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        inicio_fecha = request.POST.get('inicio_fecha', '').strip()
        inicio_hora  = request.POST.get('inicio_hora', '').strip()
        fin_fecha = request.POST.get('fin_fecha', '').strip()
        fin_hora  = request.POST.get('fin_hora', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()

        # Convertir fechas y horas
        d_ini = parse_date(inicio_fecha)
        t_ini = parse_time(inicio_hora)
        d_fin = parse_date(fin_fecha) if fin_fecha else None
        t_fin = parse_time(fin_hora) if fin_hora else None

        if not titulo or not d_ini or not t_ini:
            messages.error(request, "Título, fecha de inicio y hora de inicio son obligatorios.")
            return redirect('/panel/calendario/')

        if (d_fin and not t_fin) or (t_fin and not d_fin):
            d_fin, t_fin = None, None

        # Obtener al usuario logueado
        usuario_id = request.session.get('usuario_id')
        usuario = Usuario.objects.get(id_usuario=usuario_id)

        # Obtener su perfil administrador
        try:
            admin = Administrador.objects.get(usuario=usuario)
        except Administrador.DoesNotExist:
            messages.error(request, "Este usuario no tiene perfil de administrador.")
            return redirect('/panel/calendario/')

        # Crear el evento con el administrador real
        EventoAdmin.objects.create(
            titulo=titulo,
            inicio_fecha=d_ini,
            inicio_hora=t_ini,
            fin_fecha=d_fin,
            fin_hora=t_fin,
            descripcion=descripcion,
            creado_por=admin
        )

        messages.success(request, "Evento creado correctamente.")
        return redirect('/panel/calendario/lista/')

    return redirect('/panel/calendario/')





def listar_eventos_admin(request):
    if not _solo_admin(request):
        messages.error(request, "No tienes permisos.")
        return redirect('/login')

    eventos = EventoAdmin.objects.all().order_by('-inicio_fecha', '-inicio_hora')

    return render(request, 'administrador/listacalendarios.html', {
        'eventos': eventos
    })



def editar_evento_admin(request, id_evento):
    if not _solo_admin(request):
        messages.error(request, "No tienes permisos.")
        return redirect('/login')

    evento = EventoAdmin.objects.get(id_evento=id_evento)
    if request.method == "POST":
        titulo = request.POST.get('titulo')
        inicio_fecha = parse_date(request.POST.get('inicio_fecha'))
        inicio_hora  = parse_time(request.POST.get('inicio_hora'))
        fin_fecha    = parse_date(request.POST.get('fin_fecha')) if request.POST.get('fin_fecha') else None
        fin_hora     = parse_time(request.POST.get('fin_hora')) if request.POST.get('fin_hora') else None
        descripcion  = request.POST.get('descripcion')

        evento.titulo = titulo
        evento.inicio_fecha = inicio_fecha
        evento.inicio_hora = inicio_hora
        evento.fin_fecha = fin_fecha
        evento.fin_hora = fin_hora
        evento.descripcion = descripcion

        evento.save()

        messages.success(request, "Evento actualizado correctamente.")
        return redirect('/panel/calendario/lista/')

    return render(request, 'administrador/editar_evento.html', {'evento': evento})



def eliminar_evento_admin(request, id_evento):
    if not _solo_admin(request):
        messages.error(request, "No tienes permisos.")
        return redirect('/login')
    try:
        evento = EventoAdmin.objects.get(id_evento=id_evento)
        evento.delete()
        messages.success(request, "Evento eliminado correctamente.")
    except EventoAdmin.DoesNotExist:
        messages.error(request, "El evento no existe.")

    return redirect('/panel/calendario/lista/')


#cliente-------------------------------------------------------------------------------------------------------------

def lista_asignaciones(request):
    asignaciones = AsignacionEvento.objects.select_related("usuario", "evento")
    return render(request, 'administrador/lista_asignaciones.html', {
        'asignaciones': asignaciones
    })



def crear_asignacion(request):
    # Solo mostrar usuarios normales (no admin)
    usuarios = Usuario.objects.filter(tiporol="USUARIO")
    eventos = EventoAdmin.objects.all()

    if request.method == "POST":
        usuario_id = request.POST.get("usuario")
        evento_id = request.POST.get("evento")
        descripcion = request.POST.get("descripcion")
        fecha_asignacion = request.POST.get("fecha_asignacion")
        # Evitar duplicados
        if AsignacionEvento.objects.filter(usuario_id=usuario_id, evento_id=evento_id).exists():
            messages.error(request, "El usuario ya está asignado a este evento.")
            return redirect("/crear_asignacion/")

        AsignacionEvento.objects.create(
            usuario_id=usuario_id,
            evento_id=evento_id,
            descripcion_evento=descripcion,
            fecha_asignacion=fecha_asignacion
        )

        messages.success(request, "Asignación creada correctamente.")
        return redirect("/lista_asignaciones/")

    return render(request, 'administrador/crear_asignacion.html', {
        'usuarios': usuarios,
        'eventos': eventos,
    })


def editar_asignacion(request, id):
    asignacion = AsignacionEvento.objects.get(id_usuario_evento=id)
    usuarios = Usuario.objects.filter(tiporol="USUARIO")   # Solo mostrar usuarios normales (no administradores)
    eventos = EventoAdmin.objects.all()    # Puedes filtrar eventos si deseas, por ahora se mantienen todos:
    if request.method == "POST":
        asignacion.usuario_id = request.POST.get("usuario")
        asignacion.evento_id = request.POST.get("evento")
        asignacion.descripcion_evento = request.POST.get("descripcion")
        asignacion.fecha_asignacion = request.POST.get("fecha_asignacion")
        asignacion.save()

        messages.success(request, "Asignación actualizada correctamente.")
        return redirect("/lista_asignaciones/")

    return render(request, "administrador/editar_asignacion.html", {
        "asignacion": asignacion,
        "usuarios": usuarios,
        "eventos": eventos
    })



def eliminar_asignacion(request, id):
    asignacion = AsignacionEvento.objects.get(id_usuario_evento=id)
    asignacion.delete()
    messages.success(request, "Asignación eliminada correctamente.")
    return redirect("/lista_asignaciones/")



#provedor--------------------------------------------------------------------------------------------------------------------

def listadoproveedor(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'administrador/listadoproveedor.html', {'proveedores': proveedores})


def nuevoproveedor(request):
    return render(request, 'administrador/nuevoproveedor.html')


def guardarproveedor(request):
    nombre = request.POST['txt_nombre']
    direccion = request.POST['txt_direccion']
    telefono = request.POST['txt_telefono']
    correo = request.POST['txt_correo']
    ruc = request.POST['txt_ruc']
    estado = request.POST['txt_estado']

    Proveedor.objects.create(
        nombre_proveedor=nombre,
        direccion_proveedor=direccion,
        telefono_proveedor=telefono,
        correo_proveedor=correo,
        ruc_proveedor=ruc,
        estado_proveedor=estado
    )

    messages.success(request, "Proveedor guardado correctamente.")
    return redirect('/listadoproveedor')


def eliminarproveedor(request, id):
    proveedor = Proveedor.objects.get(id_proveedor=id)
    proveedor.delete()
    messages.success(request, "Proveedor eliminado correctamente.")
    return redirect('/listadoproveedor')


def editarproveedor(request, id):
    proveedor = Proveedor.objects.get(id_proveedor=id)
    return render(request, 'administrador/editarproveedor.html', {'proveedor': proveedor})


def procesareditarproveedor(request):
    proveedor = Proveedor.objects.get(id_proveedor=request.POST['id'])

    proveedor.nombre_proveedor = request.POST['txt_nombre']
    proveedor.direccion_proveedor = request.POST['txt_direccion']
    proveedor.telefono_proveedor = request.POST['txt_telefono']
    proveedor.correo_proveedor = request.POST['txt_correo']
    proveedor.ruc_proveedor = request.POST['txt_ruc']
    proveedor.estado_proveedor = request.POST['txt_estado']

    proveedor.save()

    messages.success(request, "Proveedor actualizado exitosamente.")
    return redirect('/listadoproveedor')


#pedido--------------------------------------------------------------------------------------------------------------------

def listadopedido(request):
    pedidos = Pedido.objects.select_related("proveedor", "evento").all()
    return render(request, 'administrador/listadopedido.html', {'pedidos': pedidos})


def nuevopedido(request):
    proveedores = Proveedor.objects.all()
    eventos = EventoAdmin.objects.all()
    return render(request, 'administrador/nuevopedido.html', {
        'proveedores': proveedores,
        'eventos': eventos
    })


def guardarpedido(request):
    descripcion = request.POST['txt_descripcion']
    proveedor_id = request.POST['txt_proveedor'] or None
    evento_id = request.POST['txt_evento']
    fecha_pedido = request.POST['txt_fecha']
    estado = request.POST['txt_estado']

    Pedido.objects.create(
        descripcion_pedido=descripcion,
        proveedor_id=proveedor_id,
        evento_id=evento_id if evento_id != "" else None,
        fecha_pedido=fecha_pedido,
        estado_pedido=estado
    )

    messages.success(request, "Pedido guardado correctamente.")
    return redirect('/listadopedido')


def eliminarpedido(request, id):
    pedido = Pedido.objects.get(id_pedido=id)
    pedido.delete()
    messages.success(request, "Pedido eliminado correctamente.")
    return redirect('/listadopedido')


def editarpedido(request, id):
    pedido = Pedido.objects.get(id_pedido=id)
    proveedores = Proveedor.objects.all()
    eventos = EventoAdmin.objects.all()

    return render(request, 'administrador/editarpedido.html', {
        'pedido': pedido,
        'proveedores': proveedores,
        'eventos': eventos
    })



def procesareditarpedido(request):
    pedido = Pedido.objects.get(id_pedido=request.POST['id'])
    pedido.descripcion_pedido = request.POST['txt_descripcion']
    pedido.proveedor_id = request.POST['txt_proveedor']if request.POST['txt_proveedor'] != "" else None
    pedido.evento_id = request.POST['txt_evento'] if request.POST['txt_evento'] != "" else None
    pedido.fecha_pedido = request.POST['txt_fecha']
    pedido.estado_pedido = request.POST['txt_estado']

    pedido.save()

    messages.success(request, "Pedido actualizado exitosamente.")
    return redirect('/listadopedido')


#DetallePedido-----------------------------------------------------------------------------------------------------

def listadodetalle(request, id_pedido):
    pedido = Pedido.objects.get(id_pedido=id_pedido)
    detalles = DetallePedido.objects.filter(pedido_id=id_pedido)
    return render(request, "administrador/listadodetalle.html", {
        "pedido": pedido,
        "detalles": detalles
    })


def nuevodetalle(request, id_pedido):
    pedido = Pedido.objects.get(id_pedido=id_pedido)
    return render(request, 'administrador/nuevodetalle.html', {'pedido': pedido})

def guardardetalle(request):

    pedido_id = request.POST["pedido_id"]
    descripcion = request.POST["txt_descripcion"]
    cantidad = request.POST["txt_cantidad"]
    precio = request.POST["txt_precio"]

    DetallePedido.objects.create(
        pedido_id=pedido_id,
        descripcion_item=descripcion,
        cantidad=cantidad,
        precio_unitario=precio
    )

    messages.success(request, "Detalle guardado correctamente.")
    return redirect(f'/listadodetalle/{pedido_id}/')


def editardetalle(request, id):
    detalle = DetallePedido.objects.get(id_detalle_pedido=id)
    return render(request, 'administrador/editardetalle.html', {
        'detalle': detalle,
        'pedido': detalle.pedido
    })


def procesareditardetalle(request):
    detalle = DetallePedido.objects.get(id_detalle_pedido=request.POST["id"])
    detalle.descripcion_item = request.POST["txt_descripcion"]
    detalle.cantidad = request.POST["txt_cantidad"]
    detalle.precio_unitario = request.POST["txt_precio"]
    detalle.save()

    messages.success(request, "Detalle actualizado correctamente.")
    return redirect(f"/listadodetalle/{detalle.pedido.id_pedido}/")


def eliminardetalle(request, id):
    detalle = DetallePedido.objects.get(id_detalle_pedido=id)
    pedido_id = detalle.pedido.id_pedido
    detalle.delete()

    messages.success(request, "Detalle eliminado correctamente.")
    return redirect(f"/listadodetalle/{pedido_id}/")


def seleccionar_pedido_detalle(request):
    pedidos = Pedido.objects.all()
    return render(request, "administrador/seleccionar_pedido.html", {"pedidos": pedidos})


def redirigir_detalle_nuevo(request):
    id_pedido = request.POST["id_pedido"]
    return redirect(f"/nuevodetalle/{id_pedido}/")



def redirigir_detalle_lista(request):
    id_pedido = request.POST["id_pedido"]
    return redirect(f"/listadodetalle/{id_pedido}/")




#factura------------------------------------------------------------------------------------------------------------------------------------

def nuevafactura(request):
    pedidos = Pedido.objects.all()
    return render(request, 'administrador/nuevafactura.html', {
        'pedidos': pedidos
    })



def crear_factura(request):
    if request.method == "POST":
        cliente_nombre = request.POST["cliente_nombre"]
        pedido_id = request.POST["pedido_id"]
        pedido = Pedido.objects.get(id_pedido=pedido_id)
        ultimo = Factura.objects.count() + 1
        numero_factura = f"001-001-{str(ultimo).zfill(9)}"

        # Crear factura
        factura = Factura.objects.create(
            cliente_nombre=cliente_nombre,
            numero_factura=numero_factura,
            pedido=pedido
        )
        # Calcular y guardar totales
        factura.recalcular_totales()
        # Redirigir a vista SOLO LECTURA
        return redirect('ver_factura', id_factura=factura.id_factura)



def ver_factura(request, id_factura):
    factura = Factura.objects.get(id_factura=id_factura)
    detalles = factura.pedido.detallepedido_set.all()
    return render(request, 'administrador/ver_factura.html', {
        'factura': factura,
        'detalles': detalles
    })




def listado_facturas(request):
    facturas = Factura.objects.all().order_by('-fecha_emision')
    return render(request, 'administrador/listadofacturas.html', {
        'facturas': facturas
    })



def eliminar_factura(request, id):
    factura = Factura.objects.get(id_factura=id)
    if factura.estado_factura == "PAGADA":
        messages.error(request, "No se puede eliminar una factura PAGADA.")
        return redirect('/listadofacturas/')

    factura.delete()
    messages.success(request, "Factura eliminada correctamente.")
    return redirect('/listadofacturas/')




#crea la factura en formato pdf -----------

from django.http import HttpResponse
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from decimal import Decimal
from .models import Factura


def factura_pdf(request, id_factura):
    factura = Factura.objects.get(id_factura=id_factura)
    detalles = factura.pedido.detallepedido_set.all()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (f'attachment; filename="Factura_{factura.numero_factura}.pdf"')

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='Titulo',
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20,
        bold=True
    ))

    styles.add(ParagraphStyle(
        name='Derecha',
        alignment=TA_RIGHT
    ))

    elementos = []

    # TÍTULO
    elementos.append(Paragraph("FACTURA", styles['Titulo']))


    # DATOS GENERALES (TABLA)
    info = [
        ["N° Factura:", factura.numero_factura],
        ["Cliente:", factura.cliente_nombre],
        ["Fecha:", factura.fecha_emision.strftime("%Y-%m-%d")],
        ["Estado:", factura.estado_factura],
    ]

    tabla_info = Table(info, colWidths=[100, 350])
    tabla_info.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica'),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))

    elementos.append(tabla_info)
    elementos.append(Spacer(1, 20))

    # TABLA DE DETALLES
    data = [["Descripción", "Cantidad", "Precio Unitario", "Subtotal"]]

    for d in detalles:
        data.append([
            d.descripcion_item,
            str(d.cantidad),
            f"$ {d.precio_unitario}",
            f"$ {d.subtotal()}"
        ])

    tabla_detalles = Table(
        data,
        colWidths=[230, 70, 100, 100]
    )

    tabla_detalles.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))

    elementos.append(tabla_detalles)
    elementos.append(Spacer(1, 20))


    # TOTALES (TABLA DERECHA)
    totales = [
        ["Subtotal:", f"$ {factura.subtotal}"],
        ["IVA (15%):", f"$ {factura.iva}"],
        ["TOTAL:", f"$ {factura.total}"],
    ]

    tabla_totales = Table(
        totales,
        colWidths=[100, 120],
        hAlign='RIGHT'
    )

    tabla_totales.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,2), (-1,2), colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))

    elementos.append(tabla_totales)

    # CONSTRUIR PDF
    doc.build(elementos)
    return response






#pago----------------------------------------------------------------------------------------------------

def registrar_pago(request, id_factura):
    factura = Factura.objects.get(id_factura=id_factura)
    if factura.estado_factura == 'PAGADA':
        messages.warning(request, "Esta factura ya fue pagada.")
        return redirect('ver_factura', factura.id_factura)

    return render(request, "administrador/registrar_pago.html", {
        "factura": factura
    })


def guardar_pago(request):
    if request.method != 'POST':
        return redirect('listado_pagos')
    
    factura = Factura.objects.get(id_factura=request.POST['factura_id'])
    monto = Decimal(request.POST['monto'])
    metodo = request.POST['metodo']
    referencia = request.POST.get('referencia')
    comprobante=request.FILES.get('comprobante')
    banco = request.POST.get('banco')

    if monto != factura.total:
        messages.error(request, 'El monto debe ser igual al total de la factura.')
        return redirect('registrar_pago', factura.id_factura)

    Pago.objects.create(
        factura=factura,
        metodo_pago=metodo,
        monto_pagado=monto,
        banco=banco,
        referencia=referencia,
        comprobante=comprobante,
        estado_pago='CONFIRMADO'
    )

    factura.estado_factura = 'PAGADA'
    factura.save()

    messages.success(request, 'Pago registrado correctamente.')
    return redirect('ver_factura', factura.id_factura)




def listado_pagos(request):
    pagos = Pago.objects.select_related('factura').order_by('-fecha_pago')
    return render(request, 'administrador/listado_pagos.html', {
        'pagos': pagos
    })



def ver_pago(request, id_pago):
    pago = Pago.objects.select_related('factura').get(id_pago=id_pago)
    return render(request, 'administrador/ver_pago.html', {
        'pago': pago
    })



def editar_pago(request, id_pago):
    pago = Pago.objects.get(id_pago=id_pago)

    if request.method == 'POST':
        pago.metodo_pago = request.POST['metodo_pago']
        pago.monto_pagado = request.POST['monto_pagado']
        pago.banco = request.POST.get('banco')
        pago.referencia = request.POST.get('referencia')
        pago.estado_pago = request.POST['estado_pago']

        if request.FILES.get('comprobante'):
            pago.comprobante = request.FILES['comprobante']

        pago.save()
        messages.success(request, 'Pago actualizado correctamente.')
        return redirect('listado_pagos')

    return render(request, 'administrador/editar_pago.html', {
        'pago': pago
    })




def eliminar_pago(request, id_pago):
    pago = Pago.objects.get(id_pago=id_pago)
    factura = pago.factura
    pago.delete()
    factura.estado_factura = 'PENDIENTE'
    factura.save()
    messages.success(request, 'Pago eliminado y factura reabierta.')
    return redirect('listado_pagos')



#salcovconducto--------------------------------------------------------------------------------

def salvoconductos(request):
    salvoconductos = Salvoconducto.objects.select_related(
        'usuario', 'vehiculo'
    )
    return render(
        request,
        'administrador/salvoconductos.html',
        {'salvoconductos': salvoconductos}
    )


def nuevosalvoconducto(request):
    if request.method == 'POST':
        usuario_id = request.POST['usuario']
        vehiculo_id = request.POST['vehiculo']
        viaje_id = request.POST['viaje']
        motivo = request.POST['motivo']
        fecha_inicio = request.POST['fecha_inicio']
        fecha_fin = request.POST['fecha_fin']
        estado = request.POST['estado']

        #  VALIDACIÓN 1: fechas
        if fecha_fin < fecha_inicio:
            messages.error(request, 'La fecha fin no puede ser menor a la fecha inicio.')
            return redirect('nuevosalvoconducto')

        #  VALIDACIÓN 2: checklist del vehículo
        tiene_checklist = ChecklistVehiculo.objects.filter(
            usuario_id=usuario_id
        ).exists()

        if not tiene_checklist:
            messages.error(request, 'El vehículo no tiene checklist registrado.')
            return redirect('nuevosalvoconducto')


        # VALIDACIÓN 3: viaje ya tiene salvoconducto
        existe_salvoconducto = Salvoconducto.objects.filter(
            viaje_id=viaje_id
        ).exists()

        if existe_salvoconducto:
            messages.error(request,' Este viaje ya tiene un salvoconducto registrado.')
            return redirect('nuevosalvoconducto')

        # guardar
        Salvoconducto.objects.create(
            usuario_id=usuario_id,
            vehiculo_id=vehiculo_id,
            viaje_id=viaje_id,
            motivo=motivo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=estado
        )

        messages.success(request, 'Salvoconducto creado correctamente.')
        return redirect('salvoconductos')

    return render(request, 'administrador/nuevosalvoconducto.html', {
        'usuarios': Usuario.objects.all(),
        'vehiculos': Vehiculo.objects.all(),
        'viajes': obtener_viajes_formateados(),
    })




def editarsalvoconducto(request, id):
    salvoconducto = Salvoconducto.objects.get(id_salvoconducto=id)
    if request.method == 'POST':
        salvoconducto.usuario_id = request.POST['usuario']
        salvoconducto.vehiculo_id = request.POST['vehiculo']
        salvoconducto.motivo = request.POST['motivo']
        salvoconducto.fecha_inicio = request.POST['fecha_inicio']
        salvoconducto.fecha_fin = request.POST['fecha_fin']
        salvoconducto.estado = request.POST['estado']
        salvoconducto.save()
        return redirect('salvoconductos')

    return render(
        request,
        'administrador/editarsalvoconducto.html',
        {
            'salvoconducto': salvoconducto,
            'usuarios': Usuario.objects.all(),
            'vehiculos': Vehiculo.objects.all(),
        }
    )


def eliminarsalvoconducto(request, id):
    Salvoconducto.objects.get(id_salvoconducto=id).delete()
    return redirect('salvoconductos')


def obtener_viajes_formateados():
    viajes = (
        Viaje.objects
        .select_related("usuario", "vehiculo", "destino")
        .order_by("-fecha_creacion")
    )

    data = []

    for viaje in viajes:
        data.append({
            "id_viaje": viaje.id_viaje,
            "usuario": f"{viaje.usuario.nombre_usuario} {viaje.usuario.apellido_usuario}",
            "vehiculo": viaje.vehiculo.matricula_vehiculo,
            "tipo_combustible": viaje.vehiculo.tipocombustible_vehiculo,
            "destino": viaje.destino.nombre_Lugarguardado,
            "fecha": viaje.fecha_creacion
        })

    return data




#pdf de salvoconducto--------------------------------------------------
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black
from reportlab.lib.utils import ImageReader
from django.http import HttpResponse
from django.utils.timezone import now

def generar_pdf_salvoconducto(request, id):
    s = Salvoconducto.objects.select_related(
        'usuario','vehiculo','viaje','viaje__origen','viaje__destino'
    ).get(id_salvoconducto=id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=salvoconducto_{id}.pdf'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    azul = HexColor("#1F4FD8")
    gris = HexColor("#444444")


    # ENCABEZADO
    p.setFont("Helvetica-Bold", 16)
    p.setFillColor(azul)
    p.drawString(50, height - 50, "SALVOCONDUCTO DE MOVILIZACIÓN")

    p.setFont("Helvetica", 10)
    p.setFillColor(black)
    p.drawString(50, height - 70, "Empresa:")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(110, height - 70, "DISTRIC")

    p.line(50, height - 80, width - 50, height - 80)

    # CUERPO
    y = height - 120
    label_x = 50
    value_x = 180
    salto = 22

    def campo(etiqueta, valor):
        nonlocal y
        p.setFont("Helvetica-Bold", 10)
        p.drawString(label_x, y, etiqueta)
        p.setFont("Helvetica", 10)
        p.drawString(value_x, y, valor)
        y -= salto

    campo("Conductor:", f"{s.usuario.nombre_usuario} {s.usuario.apellido_usuario}")
    campo("Vehículo:", f"{s.vehiculo.matricula_vehiculo} ({s.vehiculo.tipovehiculo_vehiculo})")
    campo("Destino:", s.viaje.destino.nombre_Lugarguardado)
    campo("Vigencia:", f"{s.fecha_inicio} al {s.fecha_fin}")
    campo("Estado:", s.estado_actual()) 


    p.setFont("Helvetica-Bold", 10)
    p.drawString(label_x, y, "Motivo:")
    y -= 16
    p.setFont("Helvetica", 10)
    p.drawString(label_x, y, s.motivo)


    # QR REAL
    qr_buffer = generar_qr_salvoconducto(s.id_salvoconducto)
    qr_image = ImageReader(qr_buffer)

    qr_x = width - 170
    qr_y = 130
    qr_size = 120

    p.drawImage(
        qr_image,
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        mask='auto'
    )

    p.setFont("Helvetica", 8)
    p.drawCentredString(qr_x + qr_size / 2, qr_y - 12, "Escanee para validar")


    # PIE de pagina
    p.line(50, 120, 250, 120)
    p.drawString(50, 105, "Firma responsable")

    p.setFont("Helvetica", 9)
    p.setFillColor(gris)
    p.drawString(50, 80, f"Documento generado el {now().strftime('%Y-%m-%d %H:%M')}")

    p.showPage()
    p.save()

    return response


#qr-------------------------------------------------------------------
import qrcode
from io import BytesIO

def generar_qr_salvoconducto(id):
    url = f"https://proyectodistric.onrender.com/validar/salvoconducto/{id}/"
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer



def validar_salvoconducto(request, id):
    s = Salvoconducto.objects.get(id_salvoconducto=id)
    estado_real = s.estado_actual()  
    return render(request, "administrador/validar_salvoconducto.html", {
        "salvoconducto": s,
        "estado_real": estado_real
    })




#reportes----------------------------------------------------------------------------------------------
def reporteviaje(request):
    return render(request,"administrador/reporteviaje.html",
        {"viajes": obtener_viajes_formateados()})




def reportehistorial(request):
    viajes = (
        Viaje.objects
        .select_related("usuario", "vehiculo", "origen", "destino")
        .prefetch_related("opciones")
        .order_by("-fecha_creacion")
    )

    data = []

    for viaje in viajes:
        ruta = viaje.opciones.filter(tipo="OPTIMA").first()
        data.append({
            "id": viaje.id_viaje,
            "usuario": f"{viaje.usuario.nombre_usuario} {viaje.usuario.apellido_usuario}",
            "fecha": viaje.fecha_creacion,
            "origen": f"{viaje.origen.latitud}, {viaje.origen.longitud}",
            "destino": viaje.destino.nombre_Lugarguardado,
            "vehiculo": viaje.vehiculo.matricula_vehiculo,
            "ruta": ruta.tipo if ruta else "N/A",
            "tiempo": ruta.tiempo_min if ruta else 0,
            "distancia": ruta.distancia_km if ruta else 0,
            "consumo": ruta.consumo_litros if ruta and ruta.consumo_litros else 0,
            "costo": ruta.costo_estimado if ruta and ruta.costo_estimado else 0,

        })

    return render(request, "administrador/reportehistorial.html", {
        "viajes": data
    })





#kpis--------------------------------------------------------------------------

def admin_panel(request):
    # KPI 1: lugar más repetido por cada usuario
    lugares_agrupados = (
        Lugarguardado.objects
        .values(
            'usuario_id',
            'usuario__nombre_usuario',
            'usuario__apellido_usuario',
            'nombre_Lugarguardado'
        )
        .annotate(total=Count('id_Lugarguardado'))
        .order_by('usuario_id', '-total')
    )

    resultado_por_usuario = []
    usuarios_vistos = set()

    for l in lugares_agrupados:
        uid = l['usuario_id']
        if uid in usuarios_vistos:
            continue
        usuarios_vistos.add(uid)
        resultado_por_usuario.append(l)


    kpi1_labels = []
    for l in resultado_por_usuario:
        etiqueta = (
            l['usuario__nombre_usuario'] + " " +
            l['usuario__apellido_usuario'] + " → " +
            l['nombre_Lugarguardado']
        )
        kpi1_labels.append(etiqueta)

    kpi1_data = [l['total'] for l in resultado_por_usuario]



    # KPI 2 (NUEVO): Scatter por usuario
    # X = Velocidad (km/h)
    # Y = Consumo (L/100km)
    agg = (
        RutaOpcion.objects
        .filter(viaje__usuario__tiporol="USUARIO")
        .values(
            'viaje__usuario_id',
            'viaje__usuario__nombre_usuario',
            'viaje__usuario__apellido_usuario',
        )
        .annotate(
            dist_total=Sum('distancia_km'),
            tiempo_total=Sum('tiempo_min'),
            litros_total=Sum('consumo_litros'),
        )
    )

    kpi2_points = []
    for row in agg:
        dist = row['dist_total'] or 0
        tmin = row['tiempo_total'] or 0
        litros = row['litros_total'] or 0

        # Evitar división por 0
        if dist <= 0 or tmin <= 0:
            continue

        tiempo_h = Decimal(str(tmin)) / Decimal("60")
        velocidad_kmh = (Decimal(str(dist)) / tiempo_h).quantize(Decimal("0.01"))

        # Consumo L/100km
        consumo_l_100 = ((Decimal(str(litros)) / Decimal(str(dist))) * Decimal("100")).quantize(Decimal("0.01"))

        nombre = f"{row['viaje__usuario__nombre_usuario']} {row['viaje__usuario__apellido_usuario']}"
        kpi2_points.append({
            "x": float(velocidad_kmh),
            "y": float(consumo_l_100),
            "nombre": nombre
        })

    # KPI 3: total consumo (L) por mes (TODOS los usuarios)
    meses_es = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }

    kpi3_qs = (
        RutaOpcion.objects
        .filter(viaje__usuario__tiporol="USUARIO")
        .annotate(mes=TruncMonth('viaje__fecha_creacion'))
        .values('mes')
        .annotate(total_litros=Sum('consumo_litros'))
        .order_by('mes')
    )

    kpi3_labels = []
    kpi3_data = []

    for r in kpi3_qs:
        if not r["mes"]:
            continue
        m = r["mes"]
        total = r["total_litros"] or 0
        kpi3_labels.append(f"{meses_es[m.month]} {m.year}")
        kpi3_data.append(round(float(total), 2))



    # KPI 4: total COSTO ($) por mes (TODOS los usuarios)
    kpi4_qs = (
        RutaOpcion.objects
        .filter(viaje__usuario__tiporol="USUARIO")
        .filter(costo_estimado__isnull=False)  # evita nulls
        .annotate(mes=TruncMonth('viaje__fecha_creacion'))
        .values('mes')
        .annotate(total_costo=Sum('costo_estimado'))
        .order_by('mes')
    )

    kpi4_labels = []
    kpi4_data = []

    for r in kpi4_qs:
        if not r["mes"]:
            continue
        m = r["mes"]
        total = r["total_costo"] or 0
        kpi4_labels.append(f"{meses_es[m.month]} {m.year}")
        kpi4_data.append(round(float(total), 2))



    # KPI 5: pedidos realizados por día
    dias_labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    kpi5_counts = [0, 0, 0, 0, 0, 0, 0]  # lunes=0 ... domingo=6

    pedidos_por_dia = (
        Pedido.objects
        .values('fecha_pedido')
        .annotate(total=Count('id_pedido'))
    )

    for p in pedidos_por_dia:
        fecha = p["fecha_pedido"]
        if not fecha:
            continue
        idx = fecha.weekday()  # lunes=0 ... domingo=6
        kpi5_counts[idx] += p["total"]

    kpi5_labels = dias_labels
    kpi5_data = kpi5_counts


    # KPI 6: Total litros consumidos por tipo de combustible
    kpi6_qs = (
        RutaOpcion.objects
        .filter(viaje__usuario__tiporol="USUARIO")
        .filter(combustible_tipo__isnull=False, consumo_litros__isnull=False)
        .values('combustible_tipo')
        .annotate(total_litros=Sum('consumo_litros'))
    )
    kpi6_map = {"EXTRA": 0, "DIESEL": 0, "ECOPAIS": 0, "SUPER": 0}

    for r in kpi6_qs:
        tipo = (r["combustible_tipo"] or "").upper()
        if tipo in kpi6_map:
            kpi6_map[tipo] = round(float(r["total_litros"] or 0), 2)

    kpi6_labels = list(kpi6_map.keys())
    kpi6_data = list(kpi6_map.values())



    context = {
        # KPI 1
        'kpi1_labels': json.dumps(kpi1_labels),
        'kpi1_data': json.dumps(kpi1_data),
        # KPI 2
        'kpi2_points': json.dumps(kpi2_points),
        # KPI 3
        'kpi3_labels': json.dumps(kpi3_labels),
        'kpi3_data': json.dumps(kpi3_data),
        # KPI 4
        'kpi4_labels': json.dumps(kpi4_labels),
        'kpi4_data': json.dumps(kpi4_data),
        # KPI 5
        'kpi5_labels': json.dumps(kpi5_labels),
        'kpi5_data': json.dumps(kpi5_data),
        # KPI 6
        'kpi6_labels': json.dumps(kpi6_labels),
        'kpi6_data': json.dumps(kpi6_data),

    }

    return render(request, "administrador/admin_panel.html", context)


#PWA ------------------------------------------------------------------------
from django.views.generic import TemplateView

class ManifestView(TemplateView):
    template_name = "manifest.webmanifest"
    content_type = "application/manifest+json"


class ServiceWorkerView(TemplateView):
    template_name = "service-worker.js"
    content_type = "application/javascript"



from django.shortcuts import render

def offline(request):
    return render(request, "offline.html")



#imagenes--------------------------------
from django.http import FileResponse, Http404
from django.conf import settings
import os

def media_view(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404()
    return FileResponse(open(file_path, 'rb'))
