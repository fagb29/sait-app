from django.contrib import admin
from .models import Tecnico, OrdenTrabajo, InformeMejora, ImagenInforme


# Configuración del panel de administración para Técnicos
@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    """
    Panel de administración para gestionar técnicos.
    Permite filtrar, buscar y visualizar indicadores.
    """
    list_display = [
        'codigo',
        'nombre',
        'ordenes_completadas',
        'ordenes_pendientes',
        'porcentaje_cumplimiento',
        'calificacion_promedio',
        'activo',
        'fecha_actualizacion'
    ]
    list_filter = ['activo', 'fecha_actualizacion']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['fecha_actualizacion']
    ordering = ['-porcentaje_cumplimiento', 'nombre']


# Configuración del panel de administración para Órdenes de Trabajo
@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    """
    Panel de administración para gestionar órdenes de trabajo.
    """
    list_display = [
        'numero_orden',
        'tecnico',
        'agencia',
        'empresa',
        'zona',
        'estado',
        'fecha_asignacion',
        'fecha_ejecucion'
    ]
    list_filter = ['estado', 'agencia', 'empresa', 'zona', 'fecha_asignacion', 'tecnico']
    search_fields = ['numero_orden', 'descripcion', 'direccion', 'tecnico__nombre', 'agencia', 'empresa', 'zona']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    date_hierarchy = 'fecha_asignacion'


# Inline para mostrar imágenes dentro del informe
class ImagenInformeInline(admin.TabularInline):
    """
    Permite agregar múltiples imágenes directamente desde el formulario de informe.
    """
    model = ImagenInforme
    extra = 1
    fields = ['imagen', 'descripcion', 'orden']


# Configuración del panel de administración para Informes de Mejora
@admin.register(InformeMejora)
class InformeMejoraAdmin(admin.ModelAdmin):
    """
    Panel de administración para gestionar informes de mejora.
    Incluye las imágenes asociadas mediante inline.
    """
    list_display = [
        'orden_trabajo',
        'fecha_creacion',
        'email_enviado',
        'fecha_envio_email',
        'creado_por'
    ]
    list_filter = ['email_enviado', 'fecha_creacion', 'fecha_envio_email']
    search_fields = ['orden_trabajo__numero_orden', 'comentarios']
    readonly_fields = ['fecha_creacion', 'fecha_envio_email']
    inlines = [ImagenInformeInline]
    date_hierarchy = 'fecha_creacion'


# Configuración del panel de administración para Imágenes (opcional, ya está en inline)
@admin.register(ImagenInforme)
class ImagenInformeAdmin(admin.ModelAdmin):
    """
    Panel de administración para gestionar imágenes individualmente.
    """
    list_display = ['informe', 'descripcion', 'orden', 'fecha_subida']
    list_filter = ['fecha_subida']
    search_fields = ['descripcion', 'informe__orden_trabajo__numero_orden']
    readonly_fields = ['fecha_subida']
