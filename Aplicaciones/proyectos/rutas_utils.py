from django.db.models import F, FloatField, ExpressionWrapper
from Aplicaciones.proyectos.models import NodoMapa, TramoVial
from collections import defaultdict
import heapq


# ----------------- CACHÉ DE TRAMOS -----------------

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


# ----------------- GRAFO + DIJKSTRA BÁSICO -----------------


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

    Si no hay camino, devuelve (None, inf).
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


# ------------- NODOS CERCANOS (ENGANCHE GPS–GRAFO) -------------

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


# ----------------- K MEJORES RUTAS (YEN SIMPLIFICADO) -----------------

def _copiar_grafo(grafo):
    return {u: list(ady) for u, ady in grafo.items()}


def _eliminar_arista(grafo, u, v):
    if u in grafo:
        grafo[u] = [(dest, peso) for (dest, peso) in grafo[u] if dest != v]


def _eliminar_nodos(grafo, nodos):
    nodos = set(nodos)
    for n in nodos:
        grafo.pop(n, None)

    for u in list(grafo.keys()):
        grafo[u] = [(dest, peso) for (dest, peso) in grafo[u] if dest not in nodos]


def k_mejores_rutas(grafo, origen_id, destino_id, k=5):
    """
    Devuelve una lista de hasta k rutas distintas:
    [(lista_ids_nodo, costo_tiempo_minutos), ...]
    ordenadas desde la más rápida (Dijkstra) hasta las siguientes.

    Implementa una versión simplificada del algoritmo de Yen:
    usa Dijkstra varias veces para ir encontrando rutas alternativas.
    """
    # Ruta 1 (la óptima de Dijkstra)
    primera_ruta, _ = dijkstra(grafo, origen_id, destino_id)
    if not primera_ruta:
        return []

    rutas = [primera_ruta]
    candidatos = []

    def costo_ruta(ruta_ids):
        # usamos el tiempo como costo
        _, t = calcular_metricas_ruta(ruta_ids)
        return t

    # Vamos buscando hasta k rutas
    for _ in range(1, k):
        ultima_ruta = rutas[-1]

        # Spur node = cada nodo de la ruta previa, menos el último
        for i in range(len(ultima_ruta) - 1):
            spur_node = ultima_ruta[i]
            root_path = ultima_ruta[:i + 1]

            # Copia del grafo para aplicar bloqueos
            grafo_mod = _copiar_grafo(grafo)

            # 1) Eliminar aristas que generen la misma prefijo-ruta
            for r in rutas:
                if len(r) > i and r[:i + 1] == root_path:
                    u = r[i]
                    v = r[i + 1]
                    _eliminar_arista(grafo_mod, u, v)

            # 2) Eliminar nodos del prefijo (menos el spur_node)
            nodos_bloqueados = root_path[:-1]
            _eliminar_nodos(grafo_mod, nodos_bloqueados)

            # 3) Ruta desde spur_node hasta el destino en el grafo modificado
            spur_path, _ = dijkstra(grafo_mod, spur_node, destino_id)
            if not spur_path:
                continue

            # Ruta completa = prefijo hasta spur_node (sin repetir spur_node) + spur_path
            nueva_ruta = root_path[:-1] + spur_path

            # Evitar duplicados
            if any(nueva_ruta == r for r in rutas):
                continue

            c_total = costo_ruta(nueva_ruta)
            heapq.heappush(candidatos, (c_total, nueva_ruta))

        if not candidatos:
            break

        # Tomamos el candidato más barato
        costo_k, ruta_k = heapq.heappop(candidatos)
        rutas.append(ruta_k)

    # Devolvemos rutas con su costo en tiempo
    return [(r, costo_ruta(r)) for r in rutas]
