# Comando personalizado de Django para cargar datos desde Excel
from django.core.management.base import BaseCommand
from tecnicos.utils import cargar_tecnicos_desde_excel, cargar_ordenes_desde_excel


class Command(BaseCommand):
    """
    Comando para cargar datos desde archivos Excel.

    Uso:
        python manage.py cargar_datos --tecnicos ruta/archivo.xlsx
        python manage.py cargar_datos --ordenes ruta/archivo.xlsx
        python manage.py cargar_datos --tecnicos tecnicos.xlsx --ordenes ordenes.xlsx
    """
    help = 'Carga datos de técnicos y órdenes desde archivos Excel'

    def add_arguments(self, parser):
        # Argumento para archivo de técnicos
        parser.add_argument(
            '--tecnicos',
            type=str,
            help='Ruta del archivo Excel con datos de técnicos'
        )

        # Argumento para archivo de órdenes
        parser.add_argument(
            '--ordenes',
            type=str,
            help='Ruta del archivo Excel con datos de órdenes de trabajo'
        )

    def handle(self, *args, **options):
        """
        Maneja la ejecución del comando.
        """
        archivo_tecnicos = options.get('tecnicos')
        archivo_ordenes = options.get('ordenes')

        # Validar que se proporcionó al menos un archivo
        if not archivo_tecnicos and not archivo_ordenes:
            self.stdout.write(
                self.style.ERROR('Debe proporcionar al menos un archivo (--tecnicos o --ordenes)')
            )
            return

        # Cargar técnicos si se proporcionó el archivo
        if archivo_tecnicos:
            self.stdout.write(f'Cargando técnicos desde: {archivo_tecnicos}')

            resultado = cargar_tecnicos_desde_excel(archivo_tecnicos)

            if resultado['exito']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Técnicos cargados exitosamente:\n'
                        f'  - Creados: {resultado["creados"]}\n'
                        f'  - Actualizados: {resultado["actualizados"]}\n'
                        f'  - Total procesados: {resultado["total_procesados"]}'
                    )
                )

                if resultado['errores']:
                    self.stdout.write(
                        self.style.WARNING(f'\nErrores encontrados ({len(resultado["errores"])}):')
                    )
                    for error in resultado['errores'][:10]:  # Mostrar máximo 10 errores
                        self.stdout.write(f'  - {error}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error al cargar técnicos: {resultado["mensaje_error"]}')
                )

        # Cargar órdenes si se proporcionó el archivo
        if archivo_ordenes:
            self.stdout.write(f'\nCargando órdenes desde: {archivo_ordenes}')

            resultado = cargar_ordenes_desde_excel(archivo_ordenes)

            if resultado['exito']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Órdenes cargadas exitosamente:\n'
                        f'  - Creadas: {resultado["creados"]}\n'
                        f'  - Actualizadas: {resultado["actualizados"]}\n'
                        f'  - Total procesadas: {resultado["total_procesados"]}'
                    )
                )

                if resultado['errores']:
                    self.stdout.write(
                        self.style.WARNING(f'\nErrores encontrados ({len(resultado["errores"])}):')
                    )
                    for error in resultado['errores'][:10]:
                        self.stdout.write(f'  - {error}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error al cargar órdenes: {resultado["mensaje_error"]}')
                )

        self.stdout.write(self.style.SUCCESS('\n¡Proceso completado!'))
