import json
import math
import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError
from Aplicaciones.proyectos.models import NodoMapa, TramoVial


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def clasificar_tipo_via(highway_value):
    if highway_value in ("motorway", "trunk", "primary"):
        return "PRINCIPAL"
    elif highway_value in ("secondary", "tertiary"):
        return "SECUNDARIA"
    elif highway_value in ("residential", "living_street", "service", "unclassified"):
        return "URBANA"
    else:
        return "RURAL"


def velocidad_por_tipo_via(tipo_via):
    if tipo_via == "PRINCIPAL":
        return 60.0
    elif tipo_via == "SECUNDARIA":
        return 50.0
    elif tipo_via == "URBANA":
        return 30.0
    else:
        return 40.0


class Command(BaseCommand):
    help = "Importa tramos viales (ways de OSM) desde el mismo JSON a la tabla TramoVial (optimizado para Render)"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def handle(self, *args, **options):
        file_path = options["file_path"]
        self.stdout.write(self.style.NOTICE(f"Leyendo archivo: {file_path}"))

        # ✅ para confirmar BD (Render vs local)
        self.stdout.write(
            f"DB => HOST={connection.settings_dict.get('HOST')} "
            f"NAME={connection.settings_dict.get('NAME')}"
        )

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        elementos = data.get("elements", [])

        # Cache: {osm_id: NodoMapa(pk interno)}
        # Traemos solo lo necesario para no cargar campos extra
        nodos_cache = dict(NodoMapa.objects.values_list("id_nodo", "id_nodo"))
        # Nota: como id_nodo es PK, el valor que necesitamos para FK es el mismo (id_nodo)

        total_ways = 0
        total_tramos_intentados = 0
        total_tramos_creados_aprox = 0

        BATCH_SIZE = 2000  # tramos: puedes subir a 2000-5000 según estabilidad
        batch = []

        def insertar_lote(lote):
            nonlocal total_tramos_creados_aprox
            for intento in range(1, 6):
                try:
                    TramoVial.objects.bulk_create(
                        lote,
                        ignore_conflicts=True,
                        batch_size=BATCH_SIZE
                    )
                    total_tramos_creados_aprox += len(lote)
                    return
                except OperationalError:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Se cortó SSL (intento {intento}/5). Reintentando..."
                    ))
                    connection.close()
                    time.sleep(2 * intento)
            raise OperationalError("No se pudo insertar el lote tras varios reintentos.")

        for el in elementos:
            if el.get("type") != "way":
                continue

            tags = el.get("tags", {})
            if "highway" not in tags:
                continue

            highway_value = tags.get("highway")
            tipo_via = clasificar_tipo_via(highway_value)

            nodes_list = el.get("nodes", [])
            if len(nodes_list) < 2:
                continue

            total_ways += 1

            # pares consecutivos
            for idx in range(len(nodes_list) - 1):
                osm_id_origen = nodes_list[idx]
                osm_id_destino = nodes_list[idx + 1]

                # si no existen nodos en la tabla, saltar
                if osm_id_origen not in nodos_cache or osm_id_destino not in nodos_cache:
                    continue

                total_tramos_intentados += 1

                # Obtener coordenadas de BD (solo cuando toca) — forma eficiente:
                # (si quieres más velocidad, puedo darte una versión que precargue lat/lon en dict)
                nodo_origen = NodoMapa.objects.only("id_nodo", "latitud", "longitud").get(id_nodo=osm_id_origen)
                nodo_destino = NodoMapa.objects.only("id_nodo", "latitud", "longitud").get(id_nodo=osm_id_destino)

                dist_km = haversine_km(
                    nodo_origen.latitud, nodo_origen.longitud,
                    nodo_destino.latitud, nodo_destino.longitud
                )

                vel_kmh = velocidad_por_tipo_via(tipo_via)
                tiempo_min = (dist_km / vel_kmh) * 60.0 if vel_kmh > 0 else 0.0

                # tramo ida
                batch.append(TramoVial(
                    origen_id=osm_id_origen,      # FK directo por id
                    destino_id=osm_id_destino,
                    distancia_km=dist_km,
                    tiempo_base_min=tiempo_min,
                    tipo_via=tipo_via,
                ))

                # tramo vuelta (doble sentido)
                batch.append(TramoVial(
                    origen_id=osm_id_destino,
                    destino_id=osm_id_origen,
                    distancia_km=dist_km,
                    tiempo_base_min=tiempo_min,
                    tipo_via=tipo_via,
                ))

                if len(batch) >= BATCH_SIZE:
                    insertar_lote(batch)
                    self.stdout.write(f"Ways: {total_ways} | Tramos intentados: {total_tramos_intentados}")
                    batch.clear()

        if batch:
            insertar_lote(batch)

        self.stdout.write(self.style.SUCCESS("✅ Importación de tramos completada (por lotes)"))
        self.stdout.write(f"Total ways procesados: {total_ways}")
        self.stdout.write(f"Tramos intentados (pares de nodos): {total_tramos_intentados}")
        self.stdout.write(f"Tramos insertados (aprox, incluye ignorados si ya existían): {total_tramos_creados_aprox}")

        # Conteo real en BD (útil)
        self.stdout.write(f"Total tramos actualmente en la BD: {TramoVial.objects.count()}")
