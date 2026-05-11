# URLs de la aplicación tecnicos
from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Vista principal: Listado de técnicos
    path('', views.listado_tecnicos, name='listado_tecnicos'),

    # Detalle de un técnico específico
    path('tecnico/<int:tecnico_id>/', views.detalle_tecnico, name='detalle_tecnico'),

    # Crear informe para una orden de trabajo
    path('informe/crear/<int:orden_id>/', views.crear_informe, name='crear_informe'),

    # Crear informe general (sin orden específica)
    path('informe/crear-general/', views.crear_informe_general, name='crear_informe_general'),

    # Descargar PDF de un informe
    path('informe/descargar/<int:informe_id>/', views.descargar_pdf, name='descargar_pdf'),

    # Listado de informes generados
    path('informes/', views.listado_informes, name='listado_informes'),

    # Editar y eliminar informes (solo gerencia)
    path('informe/editar/<int:informe_id>/', views.editar_informe, name='editar_informe'),
    path('informe/eliminar/<int:informe_id>/', views.eliminar_informe, name='eliminar_informe'),

    # Listados de infancias por agencia y zona
    path('infancias/agencia/', views.listado_por_agencia, name='listado_por_agencia'),
    path('infancias/zona/', views.listado_por_zona, name='listado_por_zona'),

    # Listado de órdenes con infancia
    path('ordenes/infancia/', views.listado_ordenes_infancia, name='listado_ordenes_infancia'),

    # Administración de usuarios (solo superusuario)
    path('gestion-usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('gestion-usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('gestion-usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('gestion-usuarios/eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('gestion-usuarios/cambiar-contrasena/<int:user_id>/', views.cambiar_contrasena_usuario, name='cambiar_contrasena_usuario'),

    # Accesibilidad (Ley 21.015 de Inclusión)
    path('informe/crear-accesible/', views.crear_informe_accesible, name='crear_informe_accesible'),

    # Regularización de inspecciones
    path('informe/regularizar/<int:informe_id>/', views.regularizar_informe, name='regularizar_informe'),
]
