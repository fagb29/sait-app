# Generador de PDF para informes de mejora
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from django.conf import settings
import os


def generar_pdf_informe(informe):
    """
    Genera un archivo PDF con el informe de mejora.

    Args:
        informe (InformeMejora): El informe a generar

    Returns:
        str: Ruta relativa del archivo PDF generado
    """
    # Crear directorio si no existe
    año = informe.fecha_creacion.year
    mes = informe.fecha_creacion.month
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'informes', 'pdfs', str(año), str(mes).zfill(2))
    os.makedirs(pdf_dir, exist_ok=True)

    # Nombre del archivo
    nombre_archivo = f"informe_{informe.orden_trabajo.numero_orden}_{informe.id}.pdf"
    pdf_path = os.path.join(pdf_dir, nombre_archivo)

    # Crear el documento PDF
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    story = []  # Lista de elementos del PDF

    # Estilos de texto
    styles = getSampleStyleSheet()

    # Estilo personalizado para el título
    style_titulo = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0033A0'),  # Azul Movistar
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Estilo para subtítulos
    style_subtitulo = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0033A0'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )

    # Estilo para texto normal
    style_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
    )

    # ===== ENCABEZADO =====
    titulo = Paragraph("INFORME DE MEJORA<br/>MOVISTAR", style_titulo)
    story.append(titulo)
    story.append(Spacer(1, 0.3 * inch))

    # ===== INFORMACIÓN DE LA ORDEN =====
    subtitulo_orden = Paragraph("Información de la Orden de Trabajo", style_subtitulo)
    story.append(subtitulo_orden)

    # Tabla con datos de la orden
    datos_orden = [
        ['Número de Orden:', informe.orden_trabajo.numero_orden],
        ['Técnico:', informe.orden_trabajo.tecnico.nombre],
        ['Código Técnico:', informe.orden_trabajo.tecnico.codigo],
        ['Dirección:', informe.orden_trabajo.direccion],
        ['Estado:', informe.orden_trabajo.get_estado_display()],
        ['Fecha Asignación:', informe.orden_trabajo.fecha_asignacion.strftime('%d/%m/%Y %H:%M')],
        ['Fecha Ejecución:', informe.orden_trabajo.fecha_ejecucion.strftime('%d/%m/%Y %H:%M') if informe.orden_trabajo.fecha_ejecucion else 'N/A'],
    ]

    tabla_orden = Table(datos_orden, colWidths=[2 * inch, 4 * inch])
    tabla_orden.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E6E6E6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    story.append(tabla_orden)
    story.append(Spacer(1, 0.3 * inch))

    # ===== DESCRIPCIÓN DEL TRABAJO =====
    subtitulo_desc = Paragraph("Descripción del Trabajo", style_subtitulo)
    story.append(subtitulo_desc)

    descripcion = Paragraph(informe.orden_trabajo.descripcion, style_normal)
    story.append(descripcion)
    story.append(Spacer(1, 0.3 * inch))

    # ===== COMENTARIOS Y OBSERVACIONES =====
    subtitulo_comentarios = Paragraph("Comentarios y Observaciones", style_subtitulo)
    story.append(subtitulo_comentarios)

    comentarios = Paragraph(informe.comentarios, style_normal)
    story.append(comentarios)
    story.append(Spacer(1, 0.3 * inch))

    # ===== IMÁGENES =====
    imagenes = informe.imagenes.all().order_by('orden')

    if imagenes.exists():
        subtitulo_imagenes = Paragraph("Evidencia Fotográfica", style_subtitulo)
        story.append(subtitulo_imagenes)
        story.append(Spacer(1, 0.2 * inch))

        for idx, img in enumerate(imagenes):
            try:
                if os.path.exists(img.imagen.path):
                    imagen_pdf = Image(img.imagen.path, width=6.5 * inch, height=5 * inch, kind='proportional')
                    story.append(imagen_pdf)
                    if img.descripcion:
                        desc_img = Paragraph(f"<i>{img.descripcion}</i>", style_normal)
                        story.append(desc_img)
                    story.append(Spacer(1, 0.3 * inch))
            except Exception as e:
                print(f"Error al agregar imagen al PDF: {str(e)}")

    # ===== GPS Y UBICACIÓN =====
    if informe.latitud_gps and informe.longitud_gps:
        story.append(Spacer(1, 0.3 * inch))
        subtitulo_gps = Paragraph("Ubicación GPS de la Inspección", style_subtitulo)
        story.append(subtitulo_gps)
        maps_url = f"https://maps.google.com/?q={informe.latitud_gps},{informe.longitud_gps}"
        gps_texto = Paragraph(
            f"Latitud: <b>{informe.latitud_gps}</b> | Longitud: <b>{informe.longitud_gps}</b><br/>"
            f'Verificar en mapa: <a href="{maps_url}" color="blue">{maps_url}</a>',
            style_normal
        )
        story.append(gps_texto)

    # ===== PIE DE PÁGINA =====
    story.append(Spacer(1, 0.5 * inch))

    pie_fecha = Paragraph(
        f"<i>Informe generado el {informe.fecha_creacion.strftime('%d/%m/%Y a las %H:%M')}</i>",
        style_normal
    )
    story.append(pie_fecha)

    # Construir el PDF
    doc.build(story)

    # Retornar la ruta relativa para guardarla en el modelo
    return os.path.join('informes', 'pdfs', str(año), str(mes).zfill(2), nombre_archivo)


def generar_pdf_regularizacion(reg):
    """Genera PDF para una regularización de inspección."""
    año = reg.fecha_creacion.year
    mes = reg.fecha_creacion.month
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'regularizaciones', 'pdfs', str(año), str(mes).zfill(2))
    os.makedirs(pdf_dir, exist_ok=True)

    nombre_archivo = f"regularizacion_{reg.informe_id}_{reg.id}.pdf"
    pdf_path = os.path.join(pdf_dir, nombre_archivo)

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    style_titulo = ParagraphStyle('T', parent=styles['Heading1'], fontSize=16,
        textColor=colors.HexColor('#0033A0'), spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Bold')
    style_sub = ParagraphStyle('S', parent=styles['Heading2'], fontSize=13,
        textColor=colors.HexColor('#0033A0'), spaceAfter=10, fontName='Helvetica-Bold')
    style_normal = ParagraphStyle('N', parent=styles['Normal'], fontSize=10,
        alignment=TA_JUSTIFY, spaceAfter=10)

    story.append(Paragraph("REGULARIZACIÓN DE INSPECCIÓN<br/>MOVISTAR", style_titulo))
    story.append(Spacer(1, 0.2 * inch))

    datos = [
        ['Informe original:', str(reg.informe.orden_trabajo.numero_orden)],
        ['Regularizado por:', reg.creado_por],
        ['Fecha:', reg.fecha_creacion.strftime('%d/%m/%Y %H:%M')],
    ]
    if reg.email_inspector:
        datos.append(['Email:', reg.email_inspector])
    if reg.latitud_gps:
        maps_url = f"https://maps.google.com/?q={reg.latitud_gps},{reg.longitud_gps}"
        datos.append(['GPS:', f"{reg.latitud_gps}, {reg.longitud_gps}"])
        datos.append(['Ver en mapa:', maps_url])

    tabla = Table(datos, colWidths=[2 * inch, 4 * inch])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E6E6E6')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tabla)
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Comentario de Regularización", style_sub))
    story.append(Paragraph(reg.comentario, style_normal))

    fotos = reg.fotos.all()
    if fotos.exists():
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Fotos de Regularización", style_sub))
        for foto in fotos:
            try:
                if os.path.exists(foto.imagen.path):
                    img_pdf = Image(foto.imagen.path, width=6.5 * inch, height=5 * inch, kind='proportional')
                    story.append(img_pdf)
                    story.append(Spacer(1, 0.2 * inch))
            except Exception as e:
                print(f"Error imagen regularización: {e}")

    doc.build(story)
    return os.path.join('regularizaciones', 'pdfs', str(año), str(mes).zfill(2), nombre_archivo)
