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

        for img in imagenes:
            try:
                # Verificar que la imagen existe
                if os.path.exists(img.imagen.path):
                    # Agregar la imagen al PDF (máximo 4 pulgadas de ancho)
                    imagen_pdf = Image(img.imagen.path, width=4 * inch, height=3 * inch, kind='proportional')
                    story.append(imagen_pdf)

                    # Agregar descripción si existe
                    if img.descripcion:
                        desc_img = Paragraph(f"<i>{img.descripcion}</i>", style_normal)
                        story.append(desc_img)

                    story.append(Spacer(1, 0.2 * inch))
            except Exception as e:
                print(f"Error al agregar imagen al PDF: {str(e)}")

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
