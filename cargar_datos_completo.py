# Script mejorado para cargar TODOS los datos de Movistar
import os
import django
import pandas as pd
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movistar_mejora.settings')
django.setup()

from tecnicos.models import Tecnico, OrdenTrabajo
from django.utils import timezone
from django.db import transaction

def limpiar_valor(valor):
    """Limpia y convierte valores NaN a strings vacíos"""
    if pd.isna(valor):
        return ''
    return str(valor).strip()

def limpiar_rut(rut):
    """Limpia formato de RUT"""
    rut = limpiar_valor(rut)
    # Quitar guiones y puntos
    rut = rut.replace('.', '').replace('-', '')
    return rut

def cargar_completo(archivo_path='infancia y reiterada.xlsx', limite_ordenes=None):
    """
    Carga TODOS los datos desde el Excel de Movistar.
    """
    print("="*100)
    print("CARGA COMPLETA DE DATOS MOVISTAR")
    print("="*100)

    # Leer hoja
    print("\n[PASO 1/6] Leyendo archivo Excel (puede tardar)...")
    df = pd.read_excel(archivo_path, sheet_name='p22 base')
    print(f"            Total de filas: {len(df):,}")

    # Paso 1: Crear técnicos desde AMBAS fuentes (remedy Y toa_provider)
    print("\n[PASO 2/6] Identificando tecnicos unicos...")

    # Diccionario para almacenar tecnicos unicos
    tecnicos_dict = {}

    # Fuente 1: Datos de Remedy (rmdy_)
    for _, row in df.iterrows():
        rut_remedy = limpiar_rut(row['rmdy_rut_tecnico'])
        nombre_remedy = limpiar_valor(row['rmdy_nombre_tecnico'])

        if rut_remedy and nombre_remedy and rut_remedy not in tecnicos_dict:
            tecnicos_dict[rut_remedy] = nombre_remedy

    # Fuente 2: Datos de TOA (toa_provider)
    for _, row in df.iterrows():
        rut_toa = limpiar_rut(row['toa_provider_external_id'])
        nombre_toa = limpiar_valor(row['toa_provider_name'])

        if rut_toa and nombre_toa and rut_toa not in tecnicos_dict:
            tecnicos_dict[rut_toa] = nombre_toa

    print(f"            Tecnicos unicos identificados: {len(tecnicos_dict)}")

    # Calcular estadísticas por técnico
    print("\n[PASO 3/6] Calculando estadisticas por tecnico...")

    tecnicos_stats = {}

    for _, row in df.iterrows():
        # Intentar ambos RUTs
        rut = limpiar_rut(row['rmdy_rut_tecnico'])
        if not rut:
            rut = limpiar_rut(row['toa_provider_external_id'])

        if not rut or rut not in tecnicos_dict:
            continue

        if rut not in tecnicos_stats:
            tecnicos_stats[rut] = {
                'total_ordenes': 0,
                'infancias': 0,
                'completadas': 0,
            }

        tecnicos_stats[rut]['total_ordenes'] += 1

        # Contar infancia
        infancia = row['infancia']
        if pd.notna(infancia) and infancia > 0:
            tecnicos_stats[rut]['infancias'] += 1

        # Contar completadas
        status = limpiar_valor(row['toa_status']).upper()
        if status == 'COMPLETE':
            tecnicos_stats[rut]['completadas'] += 1

    print(f"            Estadisticas calculadas para {len(tecnicos_stats)} tecnicos")

    # Crear/actualizar técnicos
    print("\n[PASO 4/6] Guardando tecnicos en base de datos...")

    tecnicos_creados = 0
    tecnicos_actualizados = 0
    tecnico_map = {}  # Mapa RUT -> objeto Tecnico

    with transaction.atomic():
        for rut, nombre in tecnicos_dict.items():
            stats = tecnicos_stats.get(rut, {'total_ordenes': 0, 'infancias': 0, 'completadas': 0})

            total = stats['total_ordenes']
            infancias = stats['infancias']
            completadas = stats['completadas']
            pendientes = total - completadas

            # Calcular métricas
            if total > 0:
                porcentaje_cumplimiento = (completadas / total) * 100
                porcentaje_infancia = (infancias / total) * 100
                porcentaje_sin_infancia = ((total - infancias) / total) * 100
                calificacion = 5.0 * (porcentaje_sin_infancia / 100)
            else:
                porcentaje_cumplimiento = 100.0
                porcentaje_infancia = 0.0
                calificacion = 5.0

            tecnico, created = Tecnico.objects.update_or_create(
                codigo=rut,
                defaults={
                    'nombre': nombre,
                    'ordenes_completadas': completadas,
                    'ordenes_pendientes': pendientes,
                    'total_infancias': infancias,
                    'porcentaje_cumplimiento': round(porcentaje_cumplimiento, 2),
                    'porcentaje_infancia': round(porcentaje_infancia, 2),
                    'calificacion_promedio': round(calificacion, 2),
                    'activo': True,
                }
            )

            tecnico_map[rut] = tecnico

            if created:
                tecnicos_creados += 1
            else:
                tecnicos_actualizados += 1

            if (tecnicos_creados + tecnicos_actualizados) % 100 == 0:
                print(f"            Procesados: {tecnicos_creados + tecnicos_actualizados}/{len(tecnicos_dict)}")

    print(f"\n            [OK] Tecnicos creados: {tecnicos_creados}")
    print(f"            [OK] Tecnicos actualizados: {tecnicos_actualizados}")

    # Cargar órdenes
    print(f"\n[PASO 5/6] Cargando ordenes de trabajo...")

    if limite_ordenes:
        df_ordenes = df.head(limite_ordenes)
        print(f"            Procesando primeras {limite_ordenes:,} ordenes...")
    else:
        df_ordenes = df
        print(f"            Procesando TODAS las {len(df):,} ordenes (puede tardar)...")

    ordenes_creadas = 0
    ordenes_actualizadas = 0
    ordenes_sin_tecnico = 0

    with transaction.atomic():
        for idx, row in df_ordenes.iterrows():
            try:
                numero_orden = limpiar_valor(row['toa_appt_number'])
                if not numero_orden:
                    continue

                # Buscar RUT del técnico
                rut = limpiar_rut(row['rmdy_rut_tecnico'])
                if not rut:
                    rut = limpiar_rut(row['toa_provider_external_id'])

                if not rut or rut not in tecnico_map:
                    ordenes_sin_tecnico += 1
                    continue

                tecnico = tecnico_map[rut]

                # Fechas
                fecha_asignacion = timezone.now()
                try:
                    fecha_asig = row['toa_xa_order_creation_date']
                    if pd.notna(fecha_asig):
                        fecha_asignacion = pd.to_datetime(fecha_asig)
                        if fecha_asignacion.tzinfo is None:
                            fecha_asignacion = timezone.make_aware(fecha_asignacion)
                except:
                    pass

                fecha_ejecucion = None
                try:
                    fecha_ejec = row['fin_actividad']
                    if pd.notna(fecha_ejec):
                        fecha_ejecucion = pd.to_datetime(fecha_ejec)
                        if fecha_ejecucion.tzinfo is None:
                            fecha_ejecucion = timezone.make_aware(fecha_ejecucion)
                except:
                    pass

                # Estado
                status = limpiar_valor(row['toa_status']).upper()
                estado = 'COMPLETADA' if status == 'COMPLETE' else 'PENDIENTE'

                # Descripción
                tipo_trabajo = limpiar_valor(row['vpi_tipo_trabajo_producto'])
                producto = limpiar_valor(row['vpi_producto'])
                descripcion_base = limpiar_valor(row['toa_descripcion'])

                if descripcion_base:
                    descripcion = descripcion_base
                else:
                    descripcion = f"{tipo_trabajo} - {producto}"

                if not descripcion or descripcion == " - ":
                    descripcion = "Orden de trabajo"

                # Dirección
                direccion = limpiar_valor(row['toa_direccion'])
                if not direccion:
                    direccion = limpiar_valor(row['toa_xa_original_agency'])
                if not direccion:
                    direccion = "Sin dirección"

                # Extraer campos adicionales
                agencia = limpiar_valor(row['toa_xa_original_agency'])
                empresa = limpiar_valor(row['toa_xr_company_name'])
                zona = limpiar_valor(row['ZONA'])

                # Extraer valor de infancia
                infancia_valor = 0
                try:
                    infancia_raw = row['infancia']
                    if pd.notna(infancia_raw):
                        infancia_valor = int(infancia_raw)
                except:
                    pass

                # Crear orden
                orden, created = OrdenTrabajo.objects.update_or_create(
                    numero_orden=numero_orden,
                    defaults={
                        'tecnico': tecnico,
                        'descripcion': descripcion[:500],
                        'direccion': direccion[:300],
                        'agencia': agencia[:200] if agencia else None,
                        'empresa': empresa[:200] if empresa else None,
                        'zona': zona[:100] if zona else None,
                        'infancia': infancia_valor,
                        'estado': estado,
                        'fecha_asignacion': fecha_asignacion,
                        'fecha_ejecucion': fecha_ejecucion,
                    }
                )

                if created:
                    ordenes_creadas += 1
                else:
                    ordenes_actualizadas += 1

                if (ordenes_creadas + ordenes_actualizadas) % 1000 == 0:
                    total_proc = ordenes_creadas + ordenes_actualizadas
                    print(f"            Procesadas: {total_proc:,}/{len(df_ordenes):,} ({(total_proc/len(df_ordenes)*100):.1f}%)")

            except Exception as e:
                if idx < 10:  # Solo mostrar primeros errores
                    print(f"            Error en fila {idx}: {str(e)}")

    print(f"\n            [OK] Ordenes creadas: {ordenes_creadas:,}")
    print(f"            [OK] Ordenes actualizadas: {ordenes_actualizadas:,}")
    print(f"            [!] Ordenes sin tecnico: {ordenes_sin_tecnico:,}")

    # Resumen
    print("\n" + "="*100)
    print("RESUMEN FINAL")
    print("="*100)

    total_tecnicos = Tecnico.objects.count()
    total_ordenes = OrdenTrabajo.objects.count()

    print(f"\n[OK] Tecnicos en base de datos: {total_tecnicos}")
    print(f"[OK] Ordenes en base de datos: {total_ordenes}")

    print("\n[TOP 15] TECNICOS POR CUMPLIMIENTO:")
    print("-"*100)

    top_tecnicos = Tecnico.objects.filter(ordenes_completadas__gt=0).order_by('-porcentaje_cumplimiento')[:15]

    for i, tec in enumerate(top_tecnicos, 1):
        print(f"  {i:2d}. {tec.nombre[:40]:40s} | {tec.codigo:15s} | {tec.porcentaje_cumplimiento:6.2f}% | {tec.ordenes_completadas:4d} ordenes | Nota: {tec.calificacion_promedio:.2f}")

    print("\n" + "="*100)
    print("[OK] PROCESO COMPLETADO EXITOSAMENTE")
    print("="*100)
    print("\nAccede a la aplicacion: http://127.0.0.1:8000/")
    print("Panel admin: http://127.0.0.1:8000/admin/ (admin/admin123)")
    print("="*100)

if __name__ == "__main__":
    import sys

    # Permitir especificar limite de ordenes
    limite = None
    if len(sys.argv) > 1:
        try:
            limite = int(sys.argv[1])
            print(f"Limitando a {limite:,} ordenes")
        except:
            pass

    cargar_completo(limite_ordenes=limite)
