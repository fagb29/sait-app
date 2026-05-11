from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Sum, F, FloatField
from django.db.models.functions import Cast
from .models import Tecnico, OrdenTrabajo, InformeMejora, ImagenInforme, RegularizacionInforme, FotoRegularizacion
from .forms import InformeForm, ImagenInformeFormSet, InformeGeneralForm, InformeAccesibleForm, RegularizacionForm
from .forms_admin import CrearUsuarioForm, EditarUsuarioForm, CambiarContrasenaForm
from .pdf_generator import generar_pdf_informe, generar_pdf_regularizacion
import os


# ===== VISTAS DE AUTENTICACIÓN =====

def login_view(request):
    """
    Vista de login personalizada con diseño Movistar.
    """
    # Si el usuario ya está autenticado, redirigir al home
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Bienvenido {user.first_name} {user.last_name}')
            # Siempre redirigir a la página principal
            return redirect('/')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'tecnicos/login.html')


@login_required
def logout_view(request):
    """
    Vista de logout.
    """
    auth_logout(request)
    messages.success(request, 'Sesión cerrada exitosamente')
    return redirect('/login/')


# ===== VISTAS PROTEGIDAS =====

# Vista principal: Listado de técnicos con sus indicadores
@login_required
def listado_tecnicos(request):
    """
    Muestra el listado de todos los técnicos con sus indicadores de desempeño.
    Permite búsqueda por código o nombre.
    Permite filtros por agencia, empresa y zona.
    """
    # Obtener parámetro de búsqueda
    busqueda = request.GET.get('buscar', '')

    # Obtener filtros
    agencia_filtro = request.GET.get('agencia', '')
    empresa_filtro = request.GET.get('empresa', '')
    zona_filtro = request.GET.get('zona', '')

    # Filtrar técnicos activos
    tecnicos = Tecnico.objects.filter(activo=True)

    # Aplicar búsqueda si existe
    if busqueda:
        tecnicos = tecnicos.filter(
            Q(codigo__icontains=busqueda) |
            Q(nombre__icontains=busqueda)
        )

    # Aplicar filtros por agencia, empresa o zona
    # Filtrar técnicos que tengan órdenes con esos criterios
    if agencia_filtro:
        tecnicos = tecnicos.filter(ordenes__agencia=agencia_filtro).distinct()

    if empresa_filtro:
        tecnicos = tecnicos.filter(ordenes__empresa=empresa_filtro).distinct()

    if zona_filtro:
        tecnicos = tecnicos.filter(ordenes__zona=zona_filtro).distinct()

    # Obtener parámetro de ordenamiento
    orden = request.GET.get('orden', 'cumplimiento_desc')

    # Aplicar ordenamiento según el parámetro
    if orden == 'infancias_asc':
        tecnicos = tecnicos.order_by('total_infancias', 'nombre')
    elif orden == 'infancias_desc':
        tecnicos = tecnicos.order_by('-total_infancias', 'nombre')
    elif orden == 'infancia_asc':
        tecnicos = tecnicos.order_by('porcentaje_infancia', 'nombre')
    elif orden == 'infancia_desc':
        tecnicos = tecnicos.order_by('-porcentaje_infancia', 'nombre')
    elif orden == 'cumplimiento_asc':
        tecnicos = tecnicos.order_by('porcentaje_cumplimiento', 'nombre')
    else:  # cumplimiento_desc (default)
        tecnicos = tecnicos.order_by('-porcentaje_cumplimiento', 'nombre')

    # Obtener listas únicas para los filtros (dinámicamente según filtros activos)
    # Filtrar las opciones de los selectores según los filtros ya aplicados
    ordenes_para_filtros = OrdenTrabajo.objects.all()

    # Si hay zona seleccionada, filtrar agencias y empresas de esa zona
    if zona_filtro:
        ordenes_para_filtros = ordenes_para_filtros.filter(zona=zona_filtro)

    # Si hay agencia seleccionada, filtrar empresas y zonas de esa agencia
    if agencia_filtro:
        ordenes_para_filtros = ordenes_para_filtros.filter(agencia=agencia_filtro)

    # Si hay empresa seleccionada, filtrar agencias y zonas de esa empresa
    if empresa_filtro:
        ordenes_para_filtros = ordenes_para_filtros.filter(empresa=empresa_filtro)

    # Obtener las listas filtradas
    agencias = ordenes_para_filtros.filter(agencia__isnull=False).values_list('agencia', flat=True).distinct().order_by('agencia')
    empresas = ordenes_para_filtros.filter(empresa__isnull=False).values_list('empresa', flat=True).distinct().order_by('empresa')
    zonas = ordenes_para_filtros.filter(zona__isnull=False).values_list('zona', flat=True).distinct().order_by('zona')

    # Contexto para el template
    context = {
        'tecnicos': tecnicos,
        'busqueda': busqueda,
        'total_tecnicos': tecnicos.count(),
        'agencia_filtro': agencia_filtro,
        'empresa_filtro': empresa_filtro,
        'zona_filtro': zona_filtro,
        'agencias': agencias,
        'empresas': empresas,
        'zonas': zonas,
        'orden': orden,
    }

    return render(request, 'tecnicos/listado_tecnicos.html', context)


# Vista: Detalle de un técnico y sus órdenes de trabajo
@login_required
def detalle_tecnico(request, tecnico_id):
    """
    Muestra el detalle de un técnico específico con todas sus órdenes de trabajo.
    Incluye filtros por estado, agencia, empresa y zona.
    """
    # Obtener el técnico
    tecnico = get_object_or_404(Tecnico, id=tecnico_id)

    # Obtener todas las órdenes del técnico
    ordenes = OrdenTrabajo.objects.filter(tecnico=tecnico).order_by('-fecha_asignacion')

    # Filtro por estado (opcional)
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        ordenes = ordenes.filter(estado=estado_filtro)

    # Filtro por agencia
    agencia_filtro = request.GET.get('agencia', '')
    if agencia_filtro:
        ordenes = ordenes.filter(agencia=agencia_filtro)

    # Filtro por empresa
    empresa_filtro = request.GET.get('empresa', '')
    if empresa_filtro:
        ordenes = ordenes.filter(empresa=empresa_filtro)

    # Filtro por zona
    zona_filtro = request.GET.get('zona', '')
    if zona_filtro:
        ordenes = ordenes.filter(zona=zona_filtro)

    # Obtener listas únicas para los selectores (dinámicamente según filtros activos)
    ordenes_para_filtros = OrdenTrabajo.objects.filter(tecnico=tecnico)

    # Si hay zona seleccionada, filtrar agencias y empresas de esa zona
    if zona_filtro:
        ordenes_para_filtros = ordenes_para_filtros.filter(zona=zona_filtro)

    # Si hay agencia seleccionada, filtrar empresas y zonas de esa agencia
    if agencia_filtro:
        ordenes_para_filtros = ordenes_para_filtros.filter(agencia=agencia_filtro)

    # Si hay empresa seleccionada, filtrar agencias y zonas de esa empresa
    if empresa_filtro:
        ordenes_para_filtros = ordenes_para_filtros.filter(empresa=empresa_filtro)

    # Obtener las listas filtradas
    agencias = ordenes_para_filtros.filter(agencia__isnull=False).values_list('agencia', flat=True).distinct().order_by('agencia')
    empresas = ordenes_para_filtros.filter(empresa__isnull=False).values_list('empresa', flat=True).distinct().order_by('empresa')
    zonas = ordenes_para_filtros.filter(zona__isnull=False).values_list('zona', flat=True).distinct().order_by('zona')

    # Contexto para el template
    context = {
        'tecnico': tecnico,
        'ordenes': ordenes,
        'estado_filtro': estado_filtro,
        'agencia_filtro': agencia_filtro,
        'empresa_filtro': empresa_filtro,
        'zona_filtro': zona_filtro,
        'agencias': agencias,
        'empresas': empresas,
        'zonas': zonas,
        'total_ordenes': ordenes.count(),
    }

    return render(request, 'tecnicos/detalle_tecnico.html', context)


# Vista: Crear informe de mejora para una orden de trabajo
@login_required
def crear_informe(request, orden_id):
    """
    Permite crear un informe de mejora para una orden de trabajo específica.
    Incluye subida de imágenes y comentarios.
    """
    # Obtener la orden de trabajo
    orden = get_object_or_404(OrdenTrabajo, id=orden_id)

    if request.method == 'POST':
        # Procesar el formulario enviado
        form = InformeForm(request.POST)
        formset = ImagenInformeFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            # Validar GPS si hay imágenes
            hay_imagenes = any(
                f.cleaned_data.get('imagen') for f in formset
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
            )
            if hay_imagenes:
                lat_str = request.POST.get('foto_latitud', '').strip()
                lng_str = request.POST.get('foto_longitud', '').strip()
                if not lat_str or not lng_str:
                    messages.error(request, 'Error de validación: Las fotos deben enviarse con geolocalización GPS activa. Active el GPS y vuelva a intentarlo.')
                    return render(request, 'tecnicos/crear_informe.html', {'orden': orden, 'form': form, 'formset': formset})

            # Crear el informe
            informe = form.save(commit=False)
            informe.orden_trabajo = orden

            # Guardar GPS
            try:
                lat_str = request.POST.get('foto_latitud', '').strip()
                lng_str = request.POST.get('foto_longitud', '').strip()
                if lat_str and lng_str:
                    informe.latitud_gps = float(lat_str)
                    informe.longitud_gps = float(lng_str)
            except (ValueError, TypeError):
                pass

            informe.save()

            # Guardar las imágenes
            imagenes = formset.save(commit=False)
            for imagen in imagenes:
                imagen.informe = informe
                imagen.save()

            # Generar el PDF
            pdf_path = generar_pdf_informe(informe)
            informe.archivo_pdf = pdf_path
            informe.save()

            # Enviar el email
            enviar_resultado = enviar_informe_por_email(informe)

            if enviar_resultado:
                destinos = settings.EMAIL_DESTINO
                if informe.email_inspector and informe.email_inspector != settings.EMAIL_DESTINO:
                    destinos += f' y {informe.email_inspector}'
                messages.success(request, f'Informe creado y enviado exitosamente a: {destinos}')
            else:
                messages.warning(request, 'Informe creado pero hubo un error al enviar el email')

            return redirect('detalle_tecnico', tecnico_id=orden.tecnico.id)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        # Mostrar formulario vacío
        form = InformeForm()
        formset = ImagenInformeFormSet()

    # Contexto para el template
    context = {
        'orden': orden,
        'form': form,
        'formset': formset,
    }

    return render(request, 'tecnicos/crear_informe.html', context)


# Vista: Descargar PDF de un informe
@login_required
def descargar_pdf(request, informe_id):
    """
    Permite descargar el PDF de un informe de mejora.
    """
    informe = get_object_or_404(InformeMejora, id=informe_id)

    if informe.archivo_pdf:
        # Verificar que el archivo existe
        if os.path.exists(informe.archivo_pdf.path):
            response = FileResponse(
                open(informe.archivo_pdf.path, 'rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="informe_{informe.orden_trabajo.numero_orden}.pdf"'
            return response
        else:
            messages.error(request, 'El archivo PDF no se encuentra disponible')
    else:
        messages.error(request, 'Este informe no tiene un PDF generado')

    return redirect('detalle_tecnico', tecnico_id=informe.orden_trabajo.tecnico.id)


# Función auxiliar: Enviar informe por email
def enviar_informe_por_email(informe):
    """
    Envía el informe PDF al destinatario principal (settings.EMAIL_DESTINO)
    y una copia al correo del inspector si fue indicado en el formulario.
    Retorna True si al menos el envío principal tuvo éxito.
    """
    asunto = f'Informe de Mejora - Orden {informe.orden_trabajo.numero_orden}'
    cuerpo = (
        f"Estimado/a,\n\n"
        f"Adjunto encontrará el informe de mejora para la siguiente orden de trabajo:\n\n"
        f"  - Número de Orden: {informe.orden_trabajo.numero_orden}\n"
        f"  - Técnico: {informe.orden_trabajo.tecnico.nombre}\n"
        f"  - Fecha de Ejecución: {informe.orden_trabajo.fecha_ejecucion.strftime('%d/%m/%Y') if informe.orden_trabajo.fecha_ejecucion else 'N/A'}\n"
        f"  - Dirección: {informe.orden_trabajo.direccion}\n"
        f"  - Inspector: {informe.creado_por}\n\n"
        f"Comentarios:\n{informe.comentarios}\n\n"
        f"Saludos cordiales,\nSistema de Gestión Movistar"
    )

    pdf_path = informe.archivo_pdf.path if informe.archivo_pdf and os.path.exists(informe.archivo_pdf.path) else None

    def _enviar(destinatarios):
        msg = EmailMessage(
            subject=asunto,
            body=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
        )
        if pdf_path:
            msg.attach_file(pdf_path)
        msg.send()

    exito = False
    try:
        _enviar([settings.EMAIL_DESTINO])
        informe.email_enviado = True
        informe.fecha_envio_email = timezone.now()
        informe.save()
        exito = True
    except Exception as e:
        print(f"Error al enviar email principal: {e}")

    # Copia al inspector si tiene correo registrado
    if informe.email_inspector and informe.email_inspector != settings.EMAIL_DESTINO:
        try:
            _enviar([informe.email_inspector])
        except Exception as e:
            print(f"Error al enviar copia al inspector: {e}")

    return exito


# Vista: Listado de informes generados
@login_required
def listado_informes(request):
    """
    Muestra el listado de todos los informes de mejora generados.
    """
    informes = InformeMejora.objects.all().select_related('orden_trabajo', 'orden_trabajo__tecnico')

    # Filtro por técnico (opcional)
    tecnico_id = request.GET.get('tecnico', '')
    if tecnico_id:
        informes = informes.filter(orden_trabajo__tecnico_id=tecnico_id)

    # Filtro por estado de envío
    enviado = request.GET.get('enviado', '')
    if enviado == 'si':
        informes = informes.filter(email_enviado=True)
    elif enviado == 'no':
        informes = informes.filter(email_enviado=False)

    # Ordenar por fecha de creación
    informes = informes.order_by('-fecha_creacion')

    # Obtener lista de técnicos para el filtro
    tecnicos = Tecnico.objects.filter(activo=True).order_by('nombre')

    puede_editar = request.user.is_superuser or request.user.groups.filter(
        name__in=['Gerencia', 'Supervisores', 'Auditores']).exists()
    puede_eliminar = request.user.is_superuser or request.user.groups.filter(name='Gerencia').exists()

    context = {
        'informes': informes,
        'tecnicos': tecnicos,
        'tecnico_id': tecnico_id,
        'enviado': enviado,
        'puede_editar': puede_editar,
        'puede_eliminar': puede_eliminar,
    }

    return render(request, 'tecnicos/listado_informes.html', context)


# Vista: Listado de infancias por agencia
@login_required
def listado_por_agencia(request):
    """
    Muestra el listado de agencias con sus indicadores de infancia.
    Agrupa las órdenes por agencia y calcula totales e infancias.
    """
    # Obtener parámetro de ordenamiento
    orden = request.GET.get('orden', 'infancia_desc')

    # Obtener agregaciones por agencia
    agencias_stats = OrdenTrabajo.objects.filter(
        agencia__isnull=False
    ).values('agencia').annotate(
        total_ordenes=Count('id'),
        total_infancias=Sum('infancia')
    )

    # Calcular porcentaje de infancia
    agencias_list = []
    for agencia in agencias_stats:
        if agencia['total_ordenes'] > 0:
            agencia['porcentaje_infancia'] = round(
                (agencia['total_infancias'] / agencia['total_ordenes']) * 100, 2
            )
        else:
            agencia['porcentaje_infancia'] = 0.0
        agencias_list.append(agencia)

    # Ordenar según el parámetro
    if orden == 'infancia_asc':
        agencias_list.sort(key=lambda x: x['porcentaje_infancia'])
    elif orden == 'infancia_desc':
        agencias_list.sort(key=lambda x: x['porcentaje_infancia'], reverse=True)
    elif orden == 'nombre_asc':
        agencias_list.sort(key=lambda x: x['agencia'])
    elif orden == 'nombre_desc':
        agencias_list.sort(key=lambda x: x['agencia'], reverse=True)

    context = {
        'agencias': agencias_list,
        'total_agencias': len(agencias_list),
        'orden': orden,
    }

    return render(request, 'tecnicos/listado_por_agencia.html', context)


# Vista: Listado de infancias por zona
@login_required
def listado_por_zona(request):
    """
    Muestra el listado de zonas con sus indicadores de infancia.
    Agrupa las órdenes por zona y calcula totales e infancias.
    """
    # Obtener parámetro de ordenamiento
    orden = request.GET.get('orden', 'infancia_desc')

    # Obtener agregaciones por zona
    zonas_stats = OrdenTrabajo.objects.filter(
        zona__isnull=False
    ).values('zona').annotate(
        total_ordenes=Count('id'),
        total_infancias=Sum('infancia')
    )

    # Calcular porcentaje de infancia
    zonas_list = []
    for zona in zonas_stats:
        if zona['total_ordenes'] > 0:
            zona['porcentaje_infancia'] = round(
                (zona['total_infancias'] / zona['total_ordenes']) * 100, 2
            )
        else:
            zona['porcentaje_infancia'] = 0.0
        zonas_list.append(zona)

    # Ordenar según el parámetro
    if orden == 'infancia_asc':
        zonas_list.sort(key=lambda x: x['porcentaje_infancia'])
    elif orden == 'infancia_desc':
        zonas_list.sort(key=lambda x: x['porcentaje_infancia'], reverse=True)
    elif orden == 'nombre_asc':
        zonas_list.sort(key=lambda x: x['zona'])
    elif orden == 'nombre_desc':
        zonas_list.sort(key=lambda x: x['zona'], reverse=True)

    context = {
        'zonas': zonas_list,
        'total_zonas': len(zonas_list),
        'orden': orden,
    }

    return render(request, 'tecnicos/listado_por_zona.html', context)


# Vista: Crear informe general
@login_required
def crear_informe_general(request):
    """
    Permite crear un informe general sin estar ligado a una orden de trabajo específica.
    """
    if request.method == 'POST':
        form = InformeGeneralForm(request.POST, request.FILES)

        if form.is_valid():
            # Crear una orden de trabajo temporal para el informe
            numero_peticion = form.cleaned_data['numero_peticion']
            tecnico_nombre = form.cleaned_data['tecnico']
            direccion = form.cleaned_data['direccion']
            comuna = form.cleaned_data['comuna']
            empresa = form.cleaned_data['empresa']
            agencia = form.cleaned_data['agencia']
            comentarios = form.cleaned_data['comentarios']
            creado_por = form.cleaned_data['creado_por']

            # Buscar o crear el técnico
            tecnico_obj = Tecnico.objects.filter(nombre__iexact=tecnico_nombre).first()

            if not tecnico_obj:
                # Crear nuevo técnico con código autogenerado
                import random
                codigo_nuevo = f"TEC-{random.randint(1000, 9999)}"
                tecnico_obj = Tecnico.objects.create(
                    codigo=codigo_nuevo,
                    nombre=tecnico_nombre,
                    activo=True
                )

            # Crear orden de trabajo
            orden = OrdenTrabajo.objects.create(
                tecnico=tecnico_obj,
                numero_orden=numero_peticion,
                descripcion=f"Informe de hallazgo - {comuna}",
                direccion=direccion,
                agencia=agencia,
                empresa=empresa,
                zona=comuna,
                estado='COMPLETADA',
                fecha_asignacion=timezone.now(),
                fecha_ejecucion=timezone.now()
            )

            email_inspector = form.cleaned_data.get('email_inspector', '')

            # Crear el informe
            informe = InformeMejora.objects.create(
                orden_trabajo=orden,
                comentarios=comentarios,
                creado_por=creado_por,
                email_inspector=email_inspector or None,
            )

            # Validar geolocalización si se subieron imágenes
            imagenes = request.FILES.getlist('imagenes')
            if imagenes:
                lat_str = request.POST.get('foto_latitud', '').strip()
                lng_str = request.POST.get('foto_longitud', '').strip()
                if not lat_str or not lng_str:
                    messages.error(request, 'Error de validación: Las fotos deben enviarse con geolocalización GPS activa. Active el GPS y vuelva a intentarlo.')
                    form = InformeGeneralForm(request.POST, request.FILES)
                    tecnicos = Tecnico.objects.filter(activo=True).order_by('nombre')
                    return render(request, 'tecnicos/crear_informe_general.html', {'form': form, 'tecnicos': tecnicos})

            if len(imagenes) > 20:
                messages.warning(request, f'Se intentaron subir {len(imagenes)} imágenes. Solo se procesarán las primeras 20.')
                imagenes = imagenes[:20]

            for idx, imagen in enumerate(imagenes):
                ImagenInforme.objects.create(
                    informe=informe,
                    imagen=imagen,
                    descripcion=f"Imagen del hallazgo {idx + 1}",
                    orden=idx
                )

            # Guardar GPS en el informe
            try:
                lat_str = request.POST.get('foto_latitud', '').strip()
                lng_str = request.POST.get('foto_longitud', '').strip()
                if lat_str and lng_str:
                    informe.latitud_gps = float(lat_str)
                    informe.longitud_gps = float(lng_str)
                    informe.save()
            except (ValueError, TypeError):
                pass

            # Generar el PDF
            pdf_path = generar_pdf_informe(informe)
            informe.archivo_pdf = pdf_path
            informe.save()

            # Enviar el email
            enviar_resultado = enviar_informe_por_email(informe)

            if enviar_resultado:
                destinos = settings.EMAIL_DESTINO
                if informe.email_inspector and informe.email_inspector != settings.EMAIL_DESTINO:
                    destinos += f' y {informe.email_inspector}'
                messages.success(request, f'Informe creado y enviado exitosamente a: {destinos}')
            else:
                messages.warning(request, 'Informe creado pero hubo un error al enviar el email')

            return redirect('listado_tecnicos')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = InformeGeneralForm()

    # Obtener lista de técnicos para el datalist
    tecnicos = Tecnico.objects.filter(activo=True).order_by('nombre')

    context = {
        'form': form,
        'tecnicos': tecnicos,
    }

    return render(request, 'tecnicos/crear_informe_general.html', context)


# Vista: Listado de órdenes con infancia
@login_required
def listado_ordenes_infancia(request):
    """
    Muestra el listado de todas las órdenes que tienen infancia (infancia > 0).
    Permite generar informes para estas órdenes.
    """
    # Obtener parámetros de filtro
    tecnico_filtro = request.GET.get('tecnico', '')
    agencia_filtro = request.GET.get('agencia', '')
    empresa_filtro = request.GET.get('empresa', '')
    zona_filtro = request.GET.get('zona', '')

    # Filtrar órdenes con infancia > 0
    ordenes = OrdenTrabajo.objects.filter(infancia__gt=0)

    # Aplicar filtros
    if tecnico_filtro:
        ordenes = ordenes.filter(tecnico_id=tecnico_filtro)

    if agencia_filtro:
        ordenes = ordenes.filter(agencia=agencia_filtro)

    if empresa_filtro:
        ordenes = ordenes.filter(empresa=empresa_filtro)

    if zona_filtro:
        ordenes = ordenes.filter(zona=zona_filtro)

    # Ordenar por fecha de asignación descendente
    ordenes = ordenes.select_related('tecnico').order_by('-fecha_asignacion')

    # Obtener listas para filtros
    tecnicos = Tecnico.objects.filter(
        activo=True,
        ordenes__infancia__gt=0
    ).distinct().order_by('nombre')

    agencias = OrdenTrabajo.objects.filter(
        infancia__gt=0,
        agencia__isnull=False
    ).values_list('agencia', flat=True).distinct().order_by('agencia')

    empresas = OrdenTrabajo.objects.filter(
        infancia__gt=0,
        empresa__isnull=False
    ).values_list('empresa', flat=True).distinct().order_by('empresa')

    zonas = OrdenTrabajo.objects.filter(
        infancia__gt=0,
        zona__isnull=False
    ).values_list('zona', flat=True).distinct().order_by('zona')

    context = {
        'ordenes': ordenes,
        'total_ordenes': ordenes.count(),
        'tecnicos': tecnicos,
        'agencias': agencias,
        'empresas': empresas,
        'zonas': zonas,
        'tecnico_filtro': tecnico_filtro,
        'agencia_filtro': agencia_filtro,
        'empresa_filtro': empresa_filtro,
        'zona_filtro': zona_filtro,
    }

    return render(request, 'tecnicos/listado_ordenes_infancia.html', context)


# Vista: Eliminar informe (solo para gerencia)
@login_required
def eliminar_informe(request, informe_id):
    """
    Permite eliminar un informe. Solo accesible para usuarios del grupo Gerencia.
    """
    # Verificar que el usuario pertenece al grupo Gerencia
    if not request.user.groups.filter(name='Gerencia').exists() and not request.user.is_superuser:
        messages.error(request, 'No tiene permisos para eliminar informes')
        return redirect('listado_informes')

    informe = get_object_or_404(InformeMejora, id=informe_id)
    tecnico_id = informe.orden_trabajo.tecnico.id

    if request.method == 'POST':
        # Eliminar el PDF si existe
        if informe.archivo_pdf:
            try:
                if os.path.exists(informe.archivo_pdf.path):
                    os.remove(informe.archivo_pdf.path)
            except Exception as e:
                print(f"Error al eliminar PDF: {e}")

        # Eliminar el informe (las imágenes se eliminan automáticamente por CASCADE)
        informe.delete()
        messages.success(request, 'Informe eliminado exitosamente')
        return redirect('listado_informes')

    return redirect('listado_informes')


# Vista: Editar informe (solo para gerencia)
@login_required
def editar_informe(request, informe_id):
    """
    Permite editar un informe existente. Solo accesible para usuarios del grupo Gerencia.
    """
    grupos_con_edicion = ['Gerencia', 'Supervisores', 'Auditores']
    if not request.user.groups.filter(name__in=grupos_con_edicion).exists() and not request.user.is_superuser:
        messages.error(request, 'No tiene permisos para editar informes')
        return redirect('listado_informes')

    informe = get_object_or_404(InformeMejora, id=informe_id)

    if request.method == 'POST':
        form = InformeForm(request.POST, instance=informe)
        formset = ImagenInformeFormSet(request.POST, request.FILES, instance=informe)

        if form.is_valid() and formset.is_valid():
            # Guardar el informe
            informe = form.save()

            # Guardar las imágenes
            imagenes = formset.save(commit=False)
            for imagen in imagenes:
                imagen.informe = informe
                imagen.save()

            # Eliminar imágenes marcadas para eliminación
            for imagen in formset.deleted_objects:
                imagen.delete()

            # Regenerar el PDF
            pdf_path = generar_pdf_informe(informe)
            informe.archivo_pdf = pdf_path
            informe.save()

            messages.success(request, 'Informe actualizado exitosamente')
            return redirect('listado_informes')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = InformeForm(instance=informe)
        formset = ImagenInformeFormSet(instance=informe)

    context = {
        'informe': informe,
        'orden': informe.orden_trabajo,
        'form': form,
        'formset': formset,
        'editando': True,
    }

    return render(request, 'tecnicos/crear_informe.html', context)


# ===== VISTAS DE ADMINISTRACIÓN DE USUARIOS (SOLO SUPERUSUARIO) =====

def es_superusuario(user):
    """Verifica si el usuario es superusuario"""
    return user.is_superuser


@login_required
@user_passes_test(es_superusuario)
def gestionar_usuarios(request):
    """
    Listado de todos los usuarios del sistema.
    Solo accesible para superusuarios.
    """
    usuarios = User.objects.all().order_by('-is_superuser', '-is_staff', 'username')

    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios.count(),
    }

    return render(request, 'tecnicos/admin/gestionar_usuarios.html', context)


@login_required
@user_passes_test(es_superusuario)
def crear_usuario(request):
    """
    Crea un nuevo usuario en el sistema.
    Solo accesible para superusuarios.
    """
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)

        if form.is_valid():
            # Crear el usuario
            user = form.save(commit=False)
            user.save()

            # Asignar grupos
            grupos = form.cleaned_data.get('groups')
            if grupos:
                user.groups.set(grupos)

            messages.success(request, f'Usuario "{user.username}" creado exitosamente')
            return redirect('gestionar_usuarios')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = CrearUsuarioForm()

    context = {
        'form': form,
        'accion': 'Crear',
    }

    return render(request, 'tecnicos/admin/form_usuario.html', context)


@login_required
@user_passes_test(es_superusuario)
def editar_usuario(request, user_id):
    """
    Edita un usuario existente.
    Solo accesible para superusuarios.
    """
    usuario = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)

        if form.is_valid():
            user = form.save()

            # Actualizar grupos
            grupos = form.cleaned_data.get('groups')
            user.groups.set(grupos)

            messages.success(request, f'Usuario "{user.username}" actualizado exitosamente')
            return redirect('gestionar_usuarios')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = EditarUsuarioForm(instance=usuario)

    context = {
        'form': form,
        'usuario': usuario,
        'accion': 'Editar',
    }

    return render(request, 'tecnicos/admin/form_usuario.html', context)


@login_required
@user_passes_test(es_superusuario)
def eliminar_usuario(request, user_id):
    """
    Elimina un usuario del sistema.
    Solo accesible para superusuarios.
    """
    usuario = get_object_or_404(User, id=user_id)

    # No permitir eliminar al propio superusuario
    if usuario.id == request.user.id:
        messages.error(request, 'No puedes eliminar tu propia cuenta')
        return redirect('gestionar_usuarios')

    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario "{username}" eliminado exitosamente')
        return redirect('gestionar_usuarios')

    return redirect('gestionar_usuarios')


@login_required
@user_passes_test(es_superusuario)
def cambiar_contrasena_usuario(request, user_id):
    """
    Cambia la contraseña de un usuario.
    Solo accesible para superusuarios.
    """
    usuario = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = CambiarContrasenaForm(request.POST)

        if form.is_valid():
            new_password = form.cleaned_data.get('new_password1')
            usuario.set_password(new_password)
            usuario.save()

            messages.success(request, f'Contraseña de "{usuario.username}" cambiada exitosamente')
            return redirect('gestionar_usuarios')
        else:
            messages.error(request, 'Por favor corrija los errores')
    else:
        form = CambiarContrasenaForm()

    context = {
        'form': form,
        'usuario': usuario,
    }

    return render(request, 'tecnicos/admin/cambiar_contrasena.html', context)


# ===== VISTAS DE ACCESIBILIDAD =====

@login_required
def crear_informe_accesible(request):
    """
    Vista para crear informes con características de accesibilidad mejoradas.
    Cumple con la Ley 21.015 de Inclusión Laboral de Personas con Discapacidad.

    Características:
    - Navegación por teclado completa
    - Compatible con lectores de pantalla (ARIA labels)
    - Dictado por voz con Web Speech API
    - Controles de alto contraste y tamaño de texto
    - Optimizado para personas con discapacidad visual
    """
    if request.method == 'POST':
        form = InformeAccesibleForm(request.POST, request.FILES)

        if form.is_valid():
            # GPS anti-fraude
            lat_str = request.POST.get('foto_latitud', '').strip()
            lng_str = request.POST.get('foto_longitud', '').strip()
            imagenes_post = request.FILES.getlist('imagenes')
            if imagenes_post and not lat_str:
                form.add_error(None, 'GPS requerido: active la ubicación del dispositivo para subir fotos.')
                return render(request, 'tecnicos/crear_informe_accesible.html', {'form': form})

            # Obtener datos del formulario
            tecnico_nombre = form.cleaned_data['tecnico']
            fecha = form.cleaned_data['fecha']
            agencia = form.cleaned_data['agencia']
            zona = form.cleaned_data['zona']
            tipo_hallazgo = form.cleaned_data['tipo_hallazgo']
            descripcion = form.cleaned_data['descripcion']
            comentarios = form.cleaned_data['comentarios']
            direccion = form.cleaned_data['direccion']
            comuna = form.cleaned_data['comuna']
            creado_por = form.cleaned_data['creado_por']

            # Buscar o crear el técnico
            tecnico_obj = Tecnico.objects.filter(nombre__iexact=tecnico_nombre).first()
            if not tecnico_obj:
                # Crear nuevo técnico
                tecnico_obj = Tecnico.objects.create(
                    codigo=f'T{timezone.now().timestamp()}',  # Código único temporal
                    nombre=tecnico_nombre,
                    zona=zona if zona else 'GENERAL'
                )

            # Generar número de petición único
            numero_peticion = f'ACC-{timezone.now().strftime("%Y%m%d%H%M%S")}'

            # Crear orden de trabajo
            orden = OrdenTrabajo.objects.create(
                numero_peticion=numero_peticion,
                tecnico=tecnico_obj,
                direccion=direccion,
                comuna=comuna,
                empresa='Movistar',
                agencia=agencia,
                estado='completada',
                infancia=False
            )

            # Crear el informe con descripción completa
            comentarios_completos = f"TIPO DE HALLAZGO: {tipo_hallazgo}\n\n"
            comentarios_completos += f"DESCRIPCIÓN:\n{descripcion}\n\n"
            if comentarios:
                comentarios_completos += f"COMENTARIOS ADICIONALES:\n{comentarios}"

            informe = InformeMejora.objects.create(
                orden_trabajo=orden,
                comentarios=comentarios_completos,
                creado_por=creado_por,
                infancia=False
            )

            # Guardar GPS si fue capturado
            if lat_str:
                try:
                    informe.latitud_gps = float(lat_str)
                    informe.longitud_gps = float(lng_str)
                    informe.save()
                except ValueError:
                    pass

            # Guardar las imágenes si existen (máximo 20)
            imagenes = request.FILES.getlist('imagenes')
            if len(imagenes) > 20:
                messages.warning(request, f'Se intentaron subir {len(imagenes)} imágenes. Solo se procesarán las primeras 20.')
                imagenes = imagenes[:20]

            for idx, imagen in enumerate(imagenes):
                ImagenInforme.objects.create(
                    informe=informe,
                    imagen=imagen,
                    descripcion=f"Evidencia fotográfica {idx + 1}",
                    orden=idx
                )

            # Generar PDF
            try:
                pdf_path = generar_pdf_informe(informe)
                informe.archivo_pdf = pdf_path
                informe.save()

                messages.success(
                    request,
                    f'¡Informe creado exitosamente! Número de petición: {numero_peticion}. '
                    f'El PDF ha sido generado y está disponible para descarga.'
                )
            except Exception as e:
                messages.warning(
                    request,
                    f'Informe creado pero hubo un error al generar el PDF: {str(e)}'
                )

            return redirect('listado_tecnicos')
    else:
        # Valores iniciales
        form = InformeAccesibleForm(initial={
            'fecha': timezone.now().date(),
            'creado_por': request.user.get_full_name() or request.user.username
        })

    context = {
        'form': form,
    }

    return render(request, 'tecnicos/crear_informe_accesible.html', context)


# ===== REGULARIZACIÓN DE INSPECCIONES =====

@login_required
def regularizar_informe(request, informe_id):
    """Permite a Supervisores, Auditores y Gerencia regularizar una inspección."""
    grupos_permitidos = ['Gerencia', 'Supervisores', 'Auditores']
    if not request.user.groups.filter(name__in=grupos_permitidos).exists() and not request.user.is_superuser:
        messages.error(request, 'No tiene permisos para regularizar inspecciones.')
        return redirect('listado_informes')

    informe = get_object_or_404(InformeMejora, id=informe_id)

    if request.method == 'POST':
        form = RegularizacionForm(request.POST, request.FILES)
        if form.is_valid():
            lat_str = request.POST.get('reg_latitud', '').strip()
            lng_str = request.POST.get('reg_longitud', '').strip()

            fotos = [
                request.FILES.get('foto1'),
                request.FILES.get('foto2'),
                request.FILES.get('foto3'),
            ]
            fotos = [f for f in fotos if f]

            if fotos and not lat_str:
                form.add_error(None, 'GPS requerido: active la ubicación para subir fotos de regularización.')
                return render(request, 'tecnicos/regularizar_informe.html', {'form': form, 'informe': informe})

            reg = RegularizacionInforme.objects.create(
                informe=informe,
                comentario=form.cleaned_data['comentario'],
                creado_por=form.cleaned_data['creado_por'],
                email_inspector=form.cleaned_data.get('email_inspector') or None,
            )

            if lat_str:
                try:
                    reg.latitud_gps = float(lat_str)
                    reg.longitud_gps = float(lng_str)
                    reg.save()
                except ValueError:
                    pass

            for idx, foto in enumerate(fotos[:3]):
                FotoRegularizacion.objects.create(regularizacion=reg, imagen=foto, orden=idx)

            # Regenerar PDF del informe original con la regularización anexada al final
            try:
                import traceback
                pdf_path = generar_pdf_regularizacion(reg)
                reg.archivo_pdf = pdf_path
                reg.save(update_fields=['archivo_pdf'])
                messages.success(request,
                    'Regularización registrada. El PDF del informe fue actualizado con las nuevas páginas.')
            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.warning(request, f'Regularización guardada, pero error al actualizar PDF: {e}')
                messages.success(request, 'Regularización registrada exitosamente.')

            return redirect('listado_informes')
    else:
        form = RegularizacionForm(initial={
            'creado_por': request.user.get_full_name() or request.user.username
        })

    return render(request, 'tecnicos/regularizar_informe.html', {'form': form, 'informe': informe})
