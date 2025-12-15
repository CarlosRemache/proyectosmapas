

from django.db.models import F, FloatField, ExpressionWrapper
from Aplicaciones.proyectos.models import NodoMapa, TramoVial
from collections import defaultdict
import heapq


# CACHÉ DE TRAMOS (para no consultar la BD muchas veces)


_tramos_cache = None
_tramos_index_cache = None


def obtener_tramos():
    """
    Devuelve todos los TramoVial en memoria (caché).
    """
    global _tramos_cache, _tramos_index_cache

    if _tramos_cache is None:
        _tramos_cache = list(TramoVial.objects.all())
        _tramos_index_cache = None  # se reconstruye cuando se pida

    return _tramos_cache


def obtener_index_tramos():
    """
    Diccionario: (origen_id, destino_id) -> TramoVial
    """
    global _tramos_index_cache

    if _tramos_index_cache is None:
        index = {}
        for t in obtener_tramos():
            index[(t.origen_id, t.destino_id)] = t
        _tramos_index_cache = index

    return _tramos_index_cache


def limpiar_cache_tramos():
    """
    Por si actualizas la red vial y quieres vaciar la caché manualmente.
    """
    global _tramos_cache, _tramos_index_cache
    _tramos_cache = None
    _tramos_index_cache = None



# CONSTRUCCIÓN DE GRAFOS


def construir_grafo():
    """
    Grafo para la ruta óptima (peso = tiempo_base_min).
    grafo[id_nodo_origen] = [(id_nodo_destino, costo_tiempo_min), ...]
    """
    grafo = defaultdict(list)

    for tramo in obtener_tramos():
        origen_id = tramo.origen_id
        destino_id = tramo.destino_id
        costo = tramo.tiempo_base_min
        grafo[origen_id].append((destino_id, costo))

    return grafo


def dijkstra(grafo, origen_id, destino_id):
    """
    Calcula la ruta de mínimo costo entre origen_id y destino_id.
    Retorna (ruta_como_lista_de_ids, costo_total).
    """
    dist = {}
    prev = {}
    heap = [(0.0, origen_id)]
    dist[origen_id] = 0.0

    while heap:
        costo_actual, nodo = heapq.heappop(heap)

        if nodo == destino_id:
            break

        if costo_actual > dist.get(nodo, float("inf")):
            continue

        for vecino, peso in grafo.get(nodo, []):
            nuevo_costo = costo_actual + peso
            if nuevo_costo < dist.get(vecino, float("inf")):
                dist[vecino] = nuevo_costo
                prev[vecino] = nodo
                heapq.heappush(heap, (nuevo_costo, vecino))

    if destino_id not in dist:
        return None, float("inf")

    # reconstruir ruta
    ruta = [destino_id]
    while ruta[-1] != origen_id:
        ruta.append(prev[ruta[-1]])
    ruta.reverse()

    return ruta, dist[destino_id]


def calcular_metricas_ruta(lista_ids_nodo):
    """
    Suma distancia_km y tiempo_base_min para los tramos de la ruta.
    """
    index_tramos = obtener_index_tramos()

    distancia_total = 0.0
    tiempo_total = 0.0

    for u, v in zip(lista_ids_nodo[:-1], lista_ids_nodo[1:]):
        tramo = index_tramos.get((u, v))
        if not tramo:
            continue
        distancia_total += tramo.distancia_km   
        tiempo_total += tramo.tiempo_base_min  

    return distancia_total, tiempo_total



# NODOS CERCANOS (para enganchar GPS con la red vial)


def nodos_mas_cercanos(lat, lon, k=5):
    """
    Devuelve una lista con los k nodos más cercanos a (lat, lon)
    según distancia euclídea aproximada en grados.
    """
    dist_expr = ExpressionWrapper(
        (F('latitud') - lat) * (F('latitud') - lat) +
        (F('longitud') - lon) * (F('longitud') - lon),
        output_field=FloatField()
    )

    return list(
        NodoMapa.objects
        .annotate(dist2=dist_expr)
        .order_by('dist2')[:k]
    )


def nodo_mas_cercano(lat, lon):
    resultados = nodos_mas_cercanos(lat, lon, k=1)
    return resultados[0] if resultados else None


#  RUTAS ALTERNATIVAS


def construir_grafo_sin_tramo(grafo, u, v):
    """
    Devuelve una copia del grafo donde se elimina SOLO el tramo u -> v
    (y v -> u si existe).
    """
    nuevo_grafo = {
        nodo: list(adyacencias)
        for nodo, adyacencias in grafo.items()
    }

    if u in nuevo_grafo:
        nuevo_grafo[u] = [
            (dest, peso)
            for (dest, peso) in nuevo_grafo[u]
            if dest != v
        ]

    if v in nuevo_grafo:
        nuevo_grafo[v] = [
            (dest, peso)
            for (dest, peso) in nuevo_grafo[v]
            if dest != u
        ]

    return nuevo_grafo


# Penalización para los tramos de la ruta óptima
PENALIZACION_RUTA_OPTIMA = 2.0  # puedes probar 2.0, 3.0, 5.0, etc.


def construir_grafo_penalizado(grafo, ruta_optima_ids, factor=PENALIZACION_RUTA_OPTIMA):
    """
    Devuelve un grafo nuevo donde los tramos pertenecientes a la ruta óptima
    tienen su peso multiplicado por 'factor', para forzar a Dijkstra a buscar
    caminos distintos si es posible.
    """
    aristas_optimas = set(zip(ruta_optima_ids[:-1], ruta_optima_ids[1:]))
    grafo_penalizado = {}

    for u, adyacencias in grafo.items():
        nueva_lista = []
        for v, peso in adyacencias:
            if (u, v) in aristas_optimas:
                nueva_lista.append((v, peso * factor))
            else:
                nueva_lista.append((v, peso))
        grafo_penalizado[u] = nueva_lista

    return grafo_penalizado


def calcular_ruta_larga(grafo, ruta_optima_ids, origen_id, destino_id):
    """
    Calcula una ruta alternativa 'larga' penalizando los tramos de la ruta
    óptima y ejecutando Dijkstra en el grafo penalizado.
    """
    if len(ruta_optima_ids) < 2:
        return None, None

    grafo_alt = construir_grafo_penalizado(grafo, ruta_optima_ids)
    ruta_alt, costo_alt = dijkstra(grafo_alt, origen_id, destino_id)

    if not ruta_alt or ruta_alt == ruta_optima_ids:
        return None, None

    return ruta_alt, costo_alt



# RUTA SEGURA (3ª RUTA)

# FACTORES DE SEGURIDAD (ajusta a tu gusto)
FACTOR_SEGURIDAD = {
    "PRINCIPAL": 0.7,    # -30% tiempo → muy favorecida
    "SECUNDARIA": 0.85,  # -15% tiempo
    "URBANA": 1.4,       # +40% tiempo → penalizamos fuerte
    "RURAL": 1.6,        # +60% tiempo
}


def peso_seguro(tramo: TramoVial) -> float:
    base = tramo.tiempo_base_min
    tipo = (tramo.tipo_via or "").upper()
    factor = FACTOR_SEGURIDAD.get(tipo, 1.0)
    return base * factor


def construir_grafo_seguro():
    """
    Grafo usando tiempo penalizado por seguridad.
    """
    grafo = defaultdict(list)
    for tramo in obtener_tramos():
        grafo[tramo.origen_id].append((tramo.destino_id, peso_seguro(tramo)))
    return grafo


def rutas_muy_similares(r1, r2, umbral_solapamiento=0.9):
    """
    True si r1 y r2 comparten la mayoría de sus tramos.
    Así evitamos mostrar rutas que visualmente son casi iguales.
    """
    if not r1 or not r2:
        return False

    e1 = set(zip(r1[:-1], r1[1:]))
    e2 = set(zip(r2[:-1], r2[1:]))

    if not e1:
        return False

    solapamiento = len(e1 & e2) / len(e1)
    return solapamiento >= umbral_solapamiento


def calcular_ruta_segura(grafo_seguro, ruta_optima_ids, ruta_larga_ids,
                         origen_id, destino_id):
    """
    Calcula una ruta 'segura' usando el grafo_seguro.
    Si coincide demasiado con la óptima o la larga, intenta forzar
    una alternativa eliminando tramos de la ruta óptima
    (priorizando URBANA / RURAL).

    Devuelve (lista_ids_ruta_segura, costo_total_minutos) o (None, None).
    """

    ruta_segura, costo_seguro = dijkstra(grafo_seguro, origen_id, destino_id)

    if not ruta_segura:
        return None, None

    if not rutas_muy_similares(ruta_segura, ruta_optima_ids) and \
       not rutas_muy_similares(ruta_segura, ruta_larga_ids or []):
        return ruta_segura, costo_seguro


    index_tramos = obtener_index_tramos()
    candidatos = []

    for u, v in zip(ruta_optima_ids[:-1], ruta_optima_ids[1:]):
        tramo = index_tramos.get((u, v))
        if not tramo:
            continue
        tipo = (tramo.tipo_via or "").upper()

        if tipo in ("URBANA", "RURAL"):
            prioridad = 2
        elif tipo in ("SECUNDARIA", "PRINCIPAL"):
            prioridad = 1
        else:
            prioridad = 0

        candidatos.append((prioridad, u, v))

    candidatos.sort(reverse=True)  #

    for prioridad, u, v in candidatos:
        grafo_alt = construir_grafo_sin_tramo(grafo_seguro, u, v)
        ruta_alt, costo_alt = dijkstra(grafo_alt, origen_id, destino_id)
        if not ruta_alt:
            continue

        if not rutas_muy_similares(ruta_alt, ruta_optima_ids) and \
           not rutas_muy_similares(ruta_alt, ruta_larga_ids or []):
            return ruta_alt, costo_alt

    return None, None
