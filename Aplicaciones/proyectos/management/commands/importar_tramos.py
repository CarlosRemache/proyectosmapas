import json
import math
from django.core.management.base import BaseCommand
from Aplicaciones.carros2.models import NodoMapa, TramoVial


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos (lat, lon)
    usando la fórmula de Haversine.
    """
    R = 6371.0  # Radio de la Tierra en km

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # distancia en km


def clasificar_tipo_via(highway_value):
    """
    Mapea el valor de 'highway' de OSM a tu campo tipo_via.
    Puedes ajustar esto a tu criterio.
    """
    if highway_value in ("motorway", "trunk", "primary"):
        return "PRINCIPAL"
    elif highway_value in ("secondary", "tertiary"):
        return "SECUNDARIA"
    elif highway_value in ("residential", "living_street", "service", "unclassified"):
        return "URBANA"
    else:
        return "RURAL"


def velocidad_por_tipo_via(tipo_via):
    """
    Velocidades promedio (ejemplo) para calcular el tiempo_base_min.
    Ajusta estos valores según la realidad de Latacunga.
    """
    if tipo_via == "PRINCIPAL":
        return 60.0  # km/h
    elif tipo_via == "SECUNDARIA":
        return 50.0
    elif tipo_via == "URBANA":
        return 30.0
    else:  # RURAL u otros
        return 40.0


class Command(BaseCommand):
    help = "Importa tramos viales (ways de OSM) desde el mismo JSON a la tabla TramoVial"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Ruta al archivo JSON exportado de Overpass (por ejemplo red_vial_latacunga.json)",
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]

        self.stdout.write(self.style.NOTICE(f"Leyendo archivo: {file_path}"))

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        elementos = data.get("elements", [])

        # Para acceso rápido a NodoMapa por id_nodo (que es el id de OSM)
        nodos_cache = {
            n.id_nodo: n
            for n in NodoMapa.objects.all()
        }

        total_ways = 0
        total_tramos_creados = 0
        total_tramos_existentes = 0
        total_tramos_intentados = 0

        for el in elementos:
            if el.get("type") != "way":
                continue

            tags = el.get("tags", {})
            if "highway" not in tags:
                continue  # solo nos interesan caminos

            highway_value = tags.get("highway")
            tipo_via = clasificar_tipo_via(highway_value)

            nodes_list = el.get("nodes", [])
            if len(nodes_list) < 2:
                continue

            total_ways += 1

            # Recorremos pares consecutivos de nodos: (n0->n1), (n1->n2), ...
            for idx in range(len(nodes_list) - 1):
                osm_id_origen = nodes_list[idx]
                osm_id_destino = nodes_list[idx + 1]

                # Verificar que ambos nodos existan en la tabla NodoMapa
                nodo_origen = nodos_cache.get(osm_id_origen)
                nodo_destino = nodos_cache.get(osm_id_destino)
                if not nodo_origen or not nodo_destino:
                    continue

                total_tramos_intentados += 1

                # Calcular distancia y tiempo
                dist_km = haversine_km(
                    nodo_origen.latitud,
                    nodo_origen.longitud,
                    nodo_destino.latitud,
                    nodo_destino.longitud,
                )

                vel_kmh = velocidad_por_tipo_via(tipo_via)
                # tiempo (minutos) = dist(km) / vel(km/h) * 60
                tiempo_min = (dist_km / vel_kmh) * 60.0 if vel_kmh > 0 else 0.0

                # Crear tramo en sentido origen -> destino
                tramo, creado = TramoVial.objects.get_or_create(
                    origen=nodo_origen,
                    destino=nodo_destino,
                    defaults={
                        "distancia_km": dist_km,
                        "tiempo_base_min": tiempo_min,
                        "tipo_via": tipo_via,
                    },
                )

                if creado:
                    total_tramos_creados += 1
                else:
                    total_tramos_existentes += 1

                # Si quieres que todas las vías sean de doble sentido por defecto,
                # puedes también crear el tramo inverso (destino -> origen).
                # OJO: si luego quieres manejar oneway, aquí habría que revisar tags['oneway'].

                tramo_inv, creado_inv = TramoVial.objects.get_or_create(
                    origen=nodo_destino,
                    destino=nodo_origen,
                    defaults={
                        "distancia_km": dist_km,
                        "tiempo_base_min": tiempo_min,
                        "tipo_via": tipo_via,
                    },
                )
                if creado_inv:
                    total_tramos_creados += 1
                else:
                    total_tramos_existentes += 1

        self.stdout.write(self.style.SUCCESS("Importación de tramos completada"))
        self.stdout.write(f"Total ways procesados: {total_ways}")
        self.stdout.write(f"Tramos intentados (pares de nodos): {total_tramos_intentados}")
        self.stdout.write(f"Tramos creados nuevos: {total_tramos_creados}")
        self.stdout.write(f"Tramos ya existentes (no duplicados): {total_tramos_existentes}")
