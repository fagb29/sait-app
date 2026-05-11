# Generador de PDF para informes de mejora
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from django.conf import settings
import os


# ─── Estilos compartidos ─────────────────────────────────────────────────────

def _estilos():
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle(
        'Titulo', parent=styles['Heading1'], fontSize=18,
        textColor=colors.HexColor('#0033A0'), spaceAfter=24,
        alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    subtitulo = ParagraphStyle(
        'Subtitulo', parent=styles['Heading2'], fontSize=13,
        textColor=colors.HexColor('#0033A0'), spaceAfter=10, fontName='Helvetica-Bold'
    )
    normal = ParagraphStyle(
        'Normal2', parent=styles['Normal'], fontSize=10,
        alignment=TA_JUSTIFY, spaceAfter=10
    )
    titulo_reg = ParagraphStyle(
        'TituloReg', parent=styles['Heading1'], fontSize=16,
        textColor=colors.HexColor('#1a7a1a'), spaceAfter=16,
        alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    return titulo, subtitulo, normal, titulo_reg


def _tabla(datos):
    t = Table(datos, colWidths=[2 * inch, 4 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E6E6E6')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    return t


# ─── Sección: contenido del informe original ─────────────────────────────────

def _story_informe(informe, titulo_st, subtitulo_st, normal_st):
    story = []

    story.append(Paragraph("INFORME DE MEJORA<br/>MOVISTAR", titulo_st))
    story.append(Spacer(1, 0.2 * inch))

    # Datos de la orden
    story.append(Paragraph("Información de la Orden de Trabajo", subtitulo_st))
    datos_orden = [
        ['Número de Orden:', informe.orden_trabajo.numero_orden],
        ['Técnico:', informe.orden_trabajo.tecnico.nombre],
        ['Código Técnico:', informe.orden_trabajo.tecnico.codigo],
        ['Dirección:', informe.orden_trabajo.direccion],
        ['Estado:', informe.orden_trabajo.get_estado_display()],
        ['Fecha Asignación:', informe.orden_trabajo.fecha_asignacion.strftime('%d/%m/%Y %H:%M')],
        ['Fecha Ejecución:', informe.orden_trabajo.fecha_ejecucion.strftime('%d/%m/%Y %H:%M') if informe.orden_trabajo.fecha_ejecucion else 'N/A'],
    ]
    if informe.creado_por:
        datos_orden.append(['Creado por:', informe.creado_por])
    if informe.email_inspector:
        datos_orden.append(['Email inspector:', informe.email_inspector])
    story.append(_tabla(datos_orden))
    story.append(Spacer(1, 0.2 * inch))

    # Descripción
    story.append(Paragraph("Descripción del Trabajo", subtitulo_st))
    story.append(Paragraph(informe.orden_trabajo.descripcion, normal_st))
    story.append(Spacer(1, 0.2 * inch))

    # Comentarios
    story.append(Paragraph("Comentarios y Observaciones", subtitulo_st))
    story.append(Paragraph(informe.comentarios, normal_st))
    story.append(Spacer(1, 0.2 * inch))

    # Imágenes originales
    imagenes = informe.imagenes.all().order_by('orden')
    if imagenes.exists():
        story.append(Paragraph("Evidencia Fotográfica de la Inspección", subtitulo_st))
        story.append(Spacer(1, 0.1 * inch))
        for img in imagenes:
            try:
                if os.path.exists(img.imagen.path):
                    story.append(Image(img.imagen.path, width=6.5 * inch, height=5 * inch, kind='proportional'))
                    if img.descripcion:
                        story.append(Paragraph(f"<i>{img.descripcion}</i>", normal_st))
                    story.append(Spacer(1, 0.2 * inch))
            except Exception as e:
                print(f"Error imagen informe: {e}")

    # GPS
    if informe.latitud_gps and informe.longitud_gps:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Ubicación GPS de la Inspección", subtitulo_st))
        maps_url = f"https://maps.google.com/?q={informe.latitud_gps},{informe.longitud_gps}"
        story.append(Paragraph(
            f"Latitud: <b>{informe.latitud_gps}</b> | Longitud: <b>{informe.longitud_gps}</b><br/>"
            f'Mapa: <a href="{maps_url}" color="blue">{maps_url}</a>',
            normal_st
        ))

    # Pie
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(
        f"<i>Informe generado el {informe.fecha_creacion.strftime('%d/%m/%Y a las %H:%M')}</i>",
        normal_st
    ))
    return story


# ─── Sección: páginas de regularización ──────────────────────────────────────

def _story_regularizacion(reg, numero, titulo_reg_st, subtitulo_st, normal_st):
    story = []

    story.append(PageBreak())
    story.append(Paragraph(
        f"REGULARIZACIÓN N° {numero}<br/>INSPECCIÓN {reg.informe.orden_trabajo.numero_orden}",
        titulo_reg_st
    ))
    story.append(Spacer(1, 0.15 * inch))

    datos = [
        ['Orden original:', reg.informe.orden_trabajo.numero_orden],
        ['Regularizado por:', reg.creado_por],
        ['Fecha regularización:', reg.fecha_creacion.strftime('%d/%m/%Y %H:%M')],
    ]
    if reg.email_inspector:
        datos.append(['Email:', reg.email_inspector])
    if reg.latitud_gps:
        maps_url = f"https://maps.google.com/?q={reg.latitud_gps},{reg.longitud_gps}"
        datos.append(['GPS:', f"{reg.latitud_gps}, {reg.longitud_gps}"])
        datos.append(['Ver en mapa:', maps_url])
    story.append(_tabla(datos))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Comentario de Regularización", subtitulo_st))
    story.append(Paragraph(reg.comentario, normal_st))

    fotos = reg.fotos.all().order_by('orden')
    if fotos.exists():
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Fotos de Regularización", subtitulo_st))
        for foto in fotos:
            try:
                if os.path.exists(foto.imagen.path):
                    story.append(Image(foto.imagen.path, width=6.5 * inch, height=5 * inch, kind='proportional'))
                    story.append(Spacer(1, 0.2 * inch))
            except Exception as e:
                print(f"Error foto regularización: {e}")

    return story


# ─── API pública ──────────────────────────────────────────────────────────────

def generar_pdf_informe(informe):
    """Genera el PDF del informe (con todas las regularizaciones si existen)."""
    año = informe.fecha_creacion.year
    mes = informe.fecha_creacion.month
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'informes', 'pdfs', str(año), str(mes).zfill(2))
    os.makedirs(pdf_dir, exist_ok=True)

    nombre_archivo = f"informe_{informe.orden_trabajo.numero_orden}_{informe.id}.pdf"
    pdf_path = os.path.join(pdf_dir, nombre_archivo)

    titulo_st, subtitulo_st, normal_st, titulo_reg_st = _estilos()

    story = _story_informe(informe, titulo_st, subtitulo_st, normal_st)

    # Anexar regularizaciones si existen
    for numero, reg in enumerate(informe.regularizaciones.all().order_by('fecha_creacion'), start=1):
        story += _story_regularizacion(reg, numero, titulo_reg_st, subtitulo_st, normal_st)

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    doc.build(story)

    return os.path.join('informes', 'pdfs', str(año), str(mes).zfill(2), nombre_archivo)


def generar_pdf_regularizacion(reg):
    """
    Regenera el PDF del informe ORIGINAL incluyendo la nueva regularización al final.
    Actualiza informe.archivo_pdf con el PDF combinado.
    """
    informe = reg.informe
    pdf_path_relativo = generar_pdf_informe(informe)

    # Actualizar el PDF del informe original para que incluya la regularización
    informe.archivo_pdf = pdf_path_relativo
    informe.save(update_fields=['archivo_pdf'])

    return pdf_path_relativo
