import json
from django.core.management.base import BaseCommand
from Aplicaciones.proyectos.models import NodoMapa # cambia 'rutas' por el nombre de tu app si es otro


class Command(BaseCommand):
    help = "Importa nodos OSM desde un archivo JSON (Overpass) a la tabla NodoMapa"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Ruta al archivo JSON exportado de Overpass (por ejemplo red_vial_latacunga.json)",
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]

        self.stdout.write(self.style.NOTICE(f"Leyendo archivo: {file_path}"))

        # 1) Cargar JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        elementos = data.get("elements", [])
        total_nodos = 0
        creados = 0
        existentes = 0

        for el in elementos:
            if el.get("type") != "node":
                continue  # solo queremos nodos

            total_nodos += 1

            osm_id = el["id"]
            lat = el["lat"]
            lon = el["lon"]

            tags = el.get("tags", {})
            nombre = tags.get("name", f"Nodo {osm_id}")

            # tipo: por ahora todo como INTERSECCION (luego podrás actualizar puntos de interés)
            tipo = "INTERSECCION"

            obj, creado = NodoMapa.objects.get_or_create(
                id_nodo=osm_id,
                defaults={
                    "nombre": nombre,
                    "latitud": lat,
                    "longitud": lon,
                    "tipo": tipo,
                },
            )

            if creado:
                creados += 1
            else:
                existentes += 1

        self.stdout.write(self.style.SUCCESS("Importación de nodos completada"))
        self.stdout.write(f"Total nodos leídos en JSON: {total_nodos}")
        self.stdout.write(f"Nodos creados nuevos: {creados}")
        self.stdout.write(f"Nodos que ya existían: {existentes}")
