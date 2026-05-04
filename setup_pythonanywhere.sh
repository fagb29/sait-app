#!/bin/bash
# Script de configuración para PythonAnywhere
# Ejecutar una sola vez después de clonar el repo

echo "=== Configurando SAIT en PythonAnywhere ==="

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env de produccion
cat > .env << 'ENVEOF'
SECRET_KEY=CAMBIA-ESTO-POR-UNA-CLAVE-SECRETA-MUY-LARGA-Y-ALEATORIA-123456789
DEBUG=False
ALLOWED_HOSTS=saitfgb.pythonanywhere.com
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_password_de_app
EMAIL_DESTINO=felipe.g.bravo@gmail.com
ENVEOF

# Aplicar migraciones
python manage.py migrate

# Crear superusuario admin
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', '', 'admin1234')
    print('Admin creado')
else:
    print('Admin ya existe')
"

# Recolectar archivos estaticos
python manage.py collectstatic --noinput

echo ""
echo "=== Configuracion completada ==="
echo "Ahora ve al dashboard de PythonAnywhere y:"
echo "1. Web > WSGI configuration file > editar"
echo "2. Web > Static files > agregar /static/ -> /home/saitfgb/sait-app/staticfiles/"
echo "3. Web > Reload"
