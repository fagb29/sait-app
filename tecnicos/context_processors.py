"""
Context processors para la aplicación tecnicos.
Provee información sobre el dispositivo del usuario en todos los templates.
"""

def device_detector(request):
    """
    Detecta si el usuario está usando un dispositivo móvil.
    Agrega variables is_mobile y is_desktop a todos los templates.
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()

    # Lista de palabras clave que indican dispositivo móvil
    mobile_keywords = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod',
        'blackberry', 'windows phone', 'webos', 'opera mini'
    ]

    # Detectar si es móvil
    is_mobile = any(keyword in user_agent for keyword in mobile_keywords)

    # Permitir al usuario forzar una versión específica mediante parámetro GET
    force_view = request.GET.get('view', None)
    if force_view == 'mobile':
        is_mobile = True
    elif force_view == 'desktop':
        is_mobile = False

    # También verificar cookie para recordar preferencia del usuario
    preferred_view = request.COOKIES.get('preferred_view', None)
    if preferred_view == 'mobile':
        is_mobile = True
    elif preferred_view == 'desktop':
        is_mobile = False

    return {
        'is_mobile': is_mobile,
        'is_desktop': not is_mobile,
        'user_agent': user_agent,
    }
