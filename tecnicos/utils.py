# Utilidades para cargar datos desde Excel
import pandas as pd
from datetime import datetime
from .models import Tecnico, OrdenTrabajo


def cargar_tecnicos_desde_excel(archivo_path):
    """
    Carga los datos de técnicos desde un archivo Excel.

    El archivo debe tener las siguientes columnas:
    - Código (o codigo): Código único del técnico
    - Nombre: Nombre completo del técnico
    - Órdenes Completadas (o ordenes_completadas): Número de órdenes completadas
    - Órdenes Pendientes (o ordenes_pendientes): Número de órdenes pendientes
    - % Cumplimiento (o porcentaje_cumplimiento): Porcentaje de cumplimiento
    - Calificación (o calificacion_promedio): Calificación promedio

    Args:
        archivo_path (str): Ruta del archivo Excel

    Returns:
        dict: Diccionario con estadísticas de carga
    """
    try:
        # Leer el archivo Excel
        df = pd.read_excel(archivo_path)

        # Normalizar nombres de columnas (quitar espacios, pasar a minúsculas)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        # Mapeo de nombres de columnas alternativas
        columnas_mapeo = {
            'código': 'codigo',
            'codigo_tecnico': 'codigo',
            'ordenes_completadas': 'ordenes_completadas',
            'órdenes_completadas': 'ordenes_completadas',
            'ordenes_pendientes': 'ordenes_pendientes',
            'órdenes_pendientes': 'ordenes_pendientes',
            '%_cumplimiento': 'porcentaje_cumplimiento',
            'porcentaje': 'porcentaje_cumplimiento',
            'calificacion': 'calificacion_promedio',
            'calificación': 'calificacion_promedio',
        }

        # Renombrar columnas según el mapeo
        df.rename(columns=columnas_mapeo, inplace=True)

        # Contadores
        creados = 0
        actualizados = 0
        errores = []

        # Iterar sobre cada fila del DataFrame
        for index, row in df.iterrows():
            try:
                # Extraer datos de la fila
                codigo = str(row.get('codigo', '')).strip()
                nombre = str(row.get('nombre', '')).strip()

                if not codigo or not nombre:
                    errores.append(f"Fila {index + 2}: Código o nombre vacío")
                    continue

                # Obtener o crear el técnico
                tecnico, created = Tecnico.objects.update_or_create(
                    codigo=codigo,
                    defaults={
                        'nombre': nombre,
                        'ordenes_completadas': int(row.get('ordenes_completadas', 0)),
                        'ordenes_pendientes': int(row.get('ordenes_pendientes', 0)),
                        'porcentaje_cumplimiento': float(row.get('porcentaje_cumplimiento', 0.0)),
                        'calificacion_promedio': float(row.get('calificacion_promedio', 0.0)),
                        'activo': True,
                    }
                )

                if created:
                    creados += 1
                else:
                    actualizados += 1

            except Exception as e:
                errores.append(f"Fila {index + 2}: {str(e)}")

        # Retornar estadísticas
        return {
            'exito': True,
            'creados': creados,
            'actualizados': actualizados,
            'errores': errores,
            'total_procesados': creados + actualizados,
        }

    except Exception as e:
        return {
            'exito': False,
            'mensaje_error': str(e),
            'creados': 0,
            'actualizados': 0,
            'errores': [],
        }


def cargar_ordenes_desde_excel(archivo_path):
    """
    Carga las órdenes de trabajo desde un archivo Excel.

    El archivo debe tener las siguientes columnas:
    - Número Orden (o numero_orden): Número único de la orden
    - Código Técnico (o codigo_tecnico): Código del técnico asignado
    - Descripción: Descripción del trabajo
    - Dirección: Dirección donde se realizó el trabajo
    - Estado: Estado de la orden (PENDIENTE, EN_PROCESO, COMPLETADA, CANCELADA)
    - Fecha Asignación (o fecha_asignacion): Fecha de asignación
    - Fecha Ejecución (o fecha_ejecucion): Fecha de ejecución (opcional)

    Args:
        archivo_path (str): Ruta del archivo Excel

    Returns:
        dict: Diccionario con estadísticas de carga
    """
    try:
        # Leer el archivo Excel
        df = pd.read_excel(archivo_path)

        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        # Mapeo de nombres de columnas
        columnas_mapeo = {
            'número_orden': 'numero_orden',
            'numero': 'numero_orden',
            'código_técnico': 'codigo_tecnico',
            'codigo': 'codigo_tecnico',
            'descripcion': 'descripcion',
            'descripción': 'descripcion',
            'direccion': 'direccion',
            'dirección': 'direccion',
            'fecha_asignacion': 'fecha_asignacion',
            'fecha_asignación': 'fecha_asignacion',
            'fecha_ejecucion': 'fecha_ejecucion',
            'fecha_ejecución': 'fecha_ejecucion',
        }

        df.rename(columns=columnas_mapeo, inplace=True)

        # Contadores
        creados = 0
        actualizados = 0
        errores = []

        # Iterar sobre cada fila
        for index, row in df.iterrows():
            try:
                numero_orden = str(row.get('numero_orden', '')).strip()
                codigo_tecnico = str(row.get('codigo_tecnico', '')).strip()

                if not numero_orden or not codigo_tecnico:
                    errores.append(f"Fila {index + 2}: Número de orden o código de técnico vacío")
                    continue

                # Buscar el técnico
                try:
                    tecnico = Tecnico.objects.get(codigo=codigo_tecnico)
                except Tecnico.DoesNotExist:
                    errores.append(f"Fila {index + 2}: Técnico con código {codigo_tecnico} no encontrado")
                    continue

                # Parsear fechas
                fecha_asignacion = pd.to_datetime(row.get('fecha_asignacion'), errors='coerce')
                if pd.isna(fecha_asignacion):
                    fecha_asignacion = datetime.now()

                fecha_ejecucion = pd.to_datetime(row.get('fecha_ejecucion'), errors='coerce')
                if pd.isna(fecha_ejecucion):
                    fecha_ejecucion = None

                # Estado
                estado = str(row.get('estado', 'PENDIENTE')).strip().upper()
                if estado not in ['PENDIENTE', 'EN_PROCESO', 'COMPLETADA', 'CANCELADA']:
                    estado = 'PENDIENTE'

                # Crear o actualizar la orden
                orden, created = OrdenTrabajo.objects.update_or_create(
                    numero_orden=numero_orden,
                    defaults={
                        'tecnico': tecnico,
                        'descripcion': str(row.get('descripcion', '')).strip(),
                        'direccion': str(row.get('direccion', '')).strip(),
                        'estado': estado,
                        'fecha_asignacion': fecha_asignacion,
                        'fecha_ejecucion': fecha_ejecucion,
                    }
                )

                if created:
                    creados += 1
                else:
                    actualizados += 1

            except Exception as e:
                errores.append(f"Fila {index + 2}: {str(e)}")

        return {
            'exito': True,
            'creados': creados,
            'actualizados': actualizados,
            'errores': errores,
            'total_procesados': creados + actualizados,
        }

    except Exception as e:
        return {
            'exito': False,
            'mensaje_error': str(e),
            'creados': 0,
            'actualizados': 0,
            'errores': [],
        }
