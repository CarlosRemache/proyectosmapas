from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario, Vehiculo, Lugarguardado, UbicacionVehiculo, PrecioCombustible,NodoMapa,Viaje,RutaOpcion,Administrador
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.timezone import now
import requests
import json
from Aplicaciones.proyectos.rutas_utils import (construir_grafo,dijkstra,calcular_metricas_ruta,nodo_mas_cercano,nodos_mas_cercanos,calcular_ruta_larga,construir_grafo_seguro,calcular_ruta_segura,)



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

            if usuario.tiporol != rol_elegido:
                messages.error(request, "Rol incorrecto para este usuario.")
                return render(request, 'login.html')


            if rol_elegido == "ADMINISTRADOR":
                try:
                    admin = Administrador.objects.get(usuario=usuario)
                except Administrador.DoesNotExist:
                    messages.error(request, "Este usuario NO tiene perfil de administrador.")
                    return render(request, 'login.html')


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

    return render(request, 'admin_panel.html')



def logout_usuario(request):
    request.session.flush()
    messages.success(request, "Sesión cerrada correctamente")
    return redirect('/login') 





def inicio(request):

    if not request.session.get('usuario_id'):
        return redirect('/login')
    
    usuario_id = request.session.get('usuario_id')
    vehiculo = Vehiculo.objects.filter(usuario_id=usuario_id).first()

    return render(request, 'inicio.html', {'vehiculo': vehiculo})



def nuevousuario(request):
    return render(request, 'nuevousuario.html')


def guardarusuario(request):
    nombre_usuario = request.POST['txt_nombre']
    apellido_usuario = request.POST['txt_apellido']
    correo_usuario = request.POST['txt_correo']
    contrasena_usuario = request.POST['txt_contrasena']
    nuevousuario=Usuario.objects.create(nombre_usuario=nombre_usuario,apellido_usuario=apellido_usuario,correo_usuario=correo_usuario,contrasena_usuario=contrasena_usuario)
    messages.success(request, "Usuario creado correctamente. Inicia sesión.")
    return redirect('/login')




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




def perfilusuario(request):
    usuario_id = request.session.get('usuario_id') 
    usuario = Usuario.objects.get(id_usuario=usuario_id) 
    return render(request, 'perfilusuario.html', {'usuario': usuario})


#---------------------------------------------------------------------------------------------------------------

def nuevovehiculo(request):
    id_usuario = request.session.get('usuario_id')
    usuario = Usuario.objects.get(id_usuario=id_usuario)
    tiene_vehiculo = Vehiculo.objects.filter(usuario=usuario).exists() 
    return render(request, 'nuevovehiculo.html', {'usuario': usuario,'tiene_vehiculo': tiene_vehiculo  })


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
    id_usuario = request.session.get('usuario_id')
    usuario = Usuario.objects.get(id_usuario=id_usuario)
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
    usuarios = Usuario.objects.get(id_usuario=id_usuario) #Busca en la base de datos al usuario
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


#----------------------------------------------------------------------------------------------buscar lugares 


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
            "q": query, 
            "format": "json", 
            "addressdetails": 1, 
            "limit": 15,
            "viewbox": "-78.7000,-0.8000,-78.5000,-1.0500",
            "bounded": 1,  
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
    usuario_id = request.session.get("usuario_id")
    usuario = Usuario.objects.get(id_usuario=usuario_id)
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
    lugar = Lugarguardado.objects.filter(id_Lugarguardado=id,   usuario_id=usuario_id  ).first()

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


    ruta = RutaOpcion.objects.filter(id_ruta_opcion=id_ruta,viaje__usuario_id=usuario_id).first()

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
            coordenadas.append([nodo.longitud, nodo.latitud])  

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




