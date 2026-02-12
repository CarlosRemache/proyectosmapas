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



def rutas_muy_similares(r1_ids, r2_ids, umbral=0.95):
    """
    Devuelve True si r1 y r2 comparten la mayoría de sus tramos.
    Sirve para descartar rutas que visualmente son casi iguales.

    - umbral=0.9 → si el 90% de las aristas son iguales, se considera "lo mismo".
    """
    if not r1_ids or not r2_ids:
        return False

    # Aristas (u -> v) de cada ruta
    e1 = set(zip(r1_ids[:-1], r1_ids[1:]))
    e2 = set(zip(r2_ids[:-1], r2_ids[1:]))

    if not e1:
        return True  # ruta muy corta, la consideramos igual

    solapamiento = len(e1 & e2) / len(e1)
    return solapamiento >= umbral




#umbral_similitud=0.9              Si pones 0.8 → aceptarás rutas un poco más parecidas (saldrán más rutas).               Si pones 0.95 → exigirás que sean muy diferentes (saldrán menos rutas).
def k_mejores_rutas(grafo,origen_id,destino_id,k=6,penalizacion_base=2.0,umbral_similitud=0.9):
    """
    Devuelve una lista de hasta k rutas distintas:
    [(lista_ids_nodo, costo_tiempo_minutos), ...]
    ordenadas desde la más rápida (Dijkstra) hacia las siguientes.

    - La 1ª ruta es SIEMPRE la óptima (Dijkstra puro).
    - Las siguientes se obtienen penalizando los tramos usados.
    - Rutas que son demasiado parecidas a alguna anterior
      (según 'umbral_similitud') se DESCARTAN.
    - Resultado: entre 1 y k rutas, según cuántas distintas existan
      realmente en el grafo.
    """

    # Copia del grafo original para poder modificar pesos
    grafo_original = {u: list(ady) for u, ady in grafo.items()}

    def dijkstra_con_grafo(g):
        return dijkstra(g, origen_id, destino_id)

    rutas = []

    # 1) Ruta óptima (Dijkstra puro)
    ruta0, costo0 = dijkstra_con_grafo(grafo_original)
    if not ruta0:
        return []

    rutas.append((ruta0, costo0))

    # 2) Rutas alternativas penalizando aristas ya usadas
    #    Usamos un número máximo de intentos para no colgarnos
    max_intentos = k * 4   # por ejemplo, 4 intentos por cada ruta deseada
    intentos = 0

    while len(rutas) < k and intentos < max_intentos:
        intentos += 1

        # Unión de todas las aristas usadas en las rutas ya aceptadas
        aristas_penalizar = set()
        for ruta_ids, _ in rutas:
            aristas_penalizar.update(zip(ruta_ids[:-1], ruta_ids[1:]))

        # Aumentamos la penalización progresivamente
        factor = penalizacion_base + intentos * 0.5

        # Construimos grafo penalizado
        grafo_penal = {}
        for u, ady in grafo_original.items():
            nueva_ady = []
            for v, peso in ady:
                if (u, v) in aristas_penalizar:
                    nueva_ady.append((v, peso * factor))
                else:
                    nueva_ady.append((v, peso))
            grafo_penal[u] = nueva_ady

        # Ejecutamos Dijkstra en el grafo penalizado
        ruta_i, costo_i = dijkstra_con_grafo(grafo_penal)
        if not ruta_i:
            break  # no hay más caminos

        # ----- FILTRO IMPORTANTE -----
        # Descartar si es igual o demasiado similar a alguna ruta anterior
        es_demasiado_parecida = False
        for ruta_existente, _ in rutas:
            if rutas_muy_similares(ruta_i, ruta_existente, umbral=umbral_similitud):
                es_demasiado_parecida = True
                break

        if es_demasiado_parecida:
            continue  # probamos otro intento con más penalización

        # Si pasó el filtro, la guardamos
        rutas.append((ruta_i, costo_i))

    return rutas
