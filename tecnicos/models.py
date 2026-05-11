from django.db import models
from django.utils import timezone


# Modelo para almacenar información de los técnicos
class Tecnico(models.Model):
    """
    Representa un técnico de Movistar con sus indicadores de desempeño.
    Los datos iniciales se cargan desde un archivo Excel.
    """
    # Información básica del técnico
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código de técnico")
    nombre = models.CharField(max_length=200, verbose_name="Nombre completo")

    # Indicadores de desempeño (pueden ajustarse según el Excel real)
    ordenes_completadas = models.IntegerField(default=0, verbose_name="Órdenes completadas")
    ordenes_pendientes = models.IntegerField(default=0, verbose_name="Órdenes pendientes")
    total_infancias = models.IntegerField(default=0, verbose_name="Total infancias")
    porcentaje_cumplimiento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="% Cumplimiento"
    )
    porcentaje_infancia = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="% Infancia"
    )
    calificacion_promedio = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name="Calificación promedio"
    )

    # Metadatos
    activo = models.BooleanField(default=True, verbose_name="Técnico activo")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Técnico"
        verbose_name_plural = "Técnicos"
        ordering = ['-porcentaje_cumplimiento', 'nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# Modelo para las órdenes de trabajo
class OrdenTrabajo(models.Model):
    """
    Representa una orden de trabajo ejecutada por un técnico.
    """
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    # Relación con el técnico
    tecnico = models.ForeignKey(
        Tecnico,
        on_delete=models.CASCADE,
        related_name='ordenes',
        verbose_name="Técnico asignado"
    )

    # Información de la orden
    numero_orden = models.CharField(max_length=100, unique=True, verbose_name="Número de orden")
    descripcion = models.TextField(verbose_name="Descripción del trabajo")
    direccion = models.CharField(max_length=300, verbose_name="Dirección")

    # Campos adicionales para filtros
    agencia = models.CharField(max_length=200, blank=True, null=True, verbose_name="Agencia")
    empresa = models.CharField(max_length=200, blank=True, null=True, verbose_name="Empresa")
    zona = models.CharField(max_length=100, blank=True, null=True, verbose_name="Zona")

    # Indicador de infancia
    infancia = models.IntegerField(default=0, verbose_name="Infancia")

    # Estado y fechas
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_asignacion = models.DateTimeField(verbose_name="Fecha de asignación")
    fecha_ejecucion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de ejecución")

    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f"Orden {self.numero_orden} - {self.tecnico.nombre}"


# Modelo para los informes de mejora
class InformeMejora(models.Model):
    """
    Almacena los informes de mejora generados para cada orden de trabajo.
    Incluye imágenes, comentarios y el PDF generado.
    """
    # Relación con la orden de trabajo
    orden_trabajo = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name='informes',
        verbose_name="Orden de trabajo"
    )

    # Contenido del informe
    comentarios = models.TextField(verbose_name="Comentarios y observaciones")

    # Archivo PDF generado
    archivo_pdf = models.FileField(
        upload_to='informes/pdfs/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Archivo PDF"
    )

    # Email del inspector que realiza la inspección
    email_inspector = models.EmailField(max_length=254, blank=True, null=True, verbose_name="Email del inspector")

    # Control de envío
    email_enviado = models.BooleanField(default=False, verbose_name="Email enviado")
    fecha_envio_email = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de envío")

    # Geolocalización al momento de la inspección
    latitud_gps = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name="Latitud GPS")
    longitud_gps = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name="Longitud GPS")

    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    creado_por = models.CharField(max_length=100, default="Sistema", verbose_name="Creado por")

    class Meta:
        verbose_name = "Informe de Mejora"
        verbose_name_plural = "Informes de Mejora"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Informe - {self.orden_trabajo.numero_orden} ({self.fecha_creacion.strftime('%d/%m/%Y')})"


# Modelo para las imágenes del informe
class ImagenInforme(models.Model):
    """
    Almacena las imágenes adjuntas a un informe de mejora.
    Permite múltiples imágenes por informe.
    """
    # Relación con el informe
    informe = models.ForeignKey(
        InformeMejora,
        on_delete=models.CASCADE,
        related_name='imagenes',
        verbose_name="Informe"
    )

    # Imagen
    imagen = models.ImageField(
        upload_to='informes/imagenes/%Y/%m/',
        verbose_name="Imagen"
    )

    # Descripción opcional de la imagen
    descripcion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Descripción de la imagen"
    )

    # Orden de visualización
    orden = models.IntegerField(default=0, verbose_name="Orden")

    # Metadatos
    fecha_subida = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de subida")

    class Meta:
        verbose_name = "Imagen de Informe"
        verbose_name_plural = "Imágenes de Informes"
        ordering = ['orden', 'fecha_subida']

    def __str__(self):
        return f"Imagen {self.orden} - {self.informe}"


class RegularizacionInforme(models.Model):
    """
    Registra la regularización de un informe: fotos + comentario de corrección.
    """
    informe = models.ForeignKey(
        InformeMejora,
        on_delete=models.CASCADE,
        related_name='regularizaciones',
        verbose_name="Informe original"
    )
    comentario = models.TextField(verbose_name="Comentario de regularización")
    creado_por = models.CharField(max_length=100, verbose_name="Creado por")
    email_inspector = models.EmailField(max_length=254, blank=True, null=True, verbose_name="Email inspector")
    latitud_gps = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud_gps = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de regularización")
    archivo_pdf = models.FileField(upload_to='regularizaciones/pdfs/%Y/%m/', null=True, blank=True)

    class Meta:
        verbose_name = "Regularización de Informe"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Regularización de {self.informe} ({self.fecha_creacion.strftime('%d/%m/%Y')})"


class FotoRegularizacion(models.Model):
    """Fotos adjuntas a una regularización (máximo 3)."""
    regularizacion = models.ForeignKey(
        RegularizacionInforme,
        on_delete=models.CASCADE,
        related_name='fotos'
    )
    imagen = models.ImageField(upload_to='regularizaciones/fotos/%Y/%m/')
    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ['orden']
