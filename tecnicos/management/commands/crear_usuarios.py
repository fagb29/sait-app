"""
Comando de Django para crear los usuarios predefinidos del sistema.
Ejecutar con: python manage.py crear_usuarios
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from tecnicos.models import Tecnico, OrdenTrabajo, InformeMejora


class Command(BaseCommand):
    help = 'Crea los usuarios y grupos predefinidos del sistema Movistar'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('=== Creando sistema de usuarios Movistar ===\n'))

        # Crear grupos si no existen
        grupo_auditores, created = Group.objects.get_or_create(name='Auditores')
        if created:
            self.stdout.write(self.style.SUCCESS('OK Grupo "Auditores" creado'))

        grupo_supervisores, created = Group.objects.get_or_create(name='Supervisores')
        if created:
            self.stdout.write(self.style.SUCCESS('OK Grupo "Supervisores" creado'))

        grupo_gerencia, created = Group.objects.get_or_create(name='Gerencia')
        if created:
            self.stdout.write(self.style.SUCCESS('OK Grupo "Gerencia" creado'))

        # Asignar permisos a grupos
        self._asignar_permisos_auditores(grupo_auditores)
        self._asignar_permisos_supervisores(grupo_supervisores)
        self._asignar_permisos_gerencia(grupo_gerencia)

        # Crear usuarios
        usuarios_creados = []

        # 1. Usuario AUDITORES
        usuario_auditores, created = User.objects.get_or_create(
            username='auditores_movistar',
            defaults={
                'first_name': 'Auditor',
                'last_name': 'Movistar',
                'email': 'auditores@movistar.cl',
                'is_staff': False,
                'is_active': True,
            }
        )
        if created:
            usuario_auditores.set_password('auditores1234')
            usuario_auditores.save()
            usuario_auditores.groups.add(grupo_auditores)
            usuarios_creados.append({
                'usuario': 'auditores_movistar',
                'clave': 'auditores1234',
                'rol': 'Auditores',
                'permisos': 'Ver técnicos, órdenes e informes'
            })
            self.stdout.write(self.style.SUCCESS('OK Usuario "auditores_movistar" creado'))
        else:
            self.stdout.write(self.style.WARNING('WARNING Usuario "auditores_movistar" ya existe'))

        # 2. Usuario SUPERVISORES
        usuario_supervisores, created = User.objects.get_or_create(
            username='supervisores_movistar',
            defaults={
                'first_name': 'Supervisor',
                'last_name': 'Movistar',
                'email': 'supervisores@movistar.cl',
                'is_staff': False,
                'is_active': True,
            }
        )
        if created:
            usuario_supervisores.set_password('supervisores1234')
            usuario_supervisores.save()
            usuario_supervisores.groups.add(grupo_supervisores)
            usuarios_creados.append({
                'usuario': 'supervisores_movistar',
                'clave': 'supervisores1234',
                'rol': 'Supervisores',
                'permisos': 'Ver y crear informes, modificar órdenes'
            })
            self.stdout.write(self.style.SUCCESS('OK Usuario "supervisores_movistar" creado'))
        else:
            self.stdout.write(self.style.WARNING('WARNING Usuario "supervisores_movistar" ya existe'))

        # 3. Usuario GERENCIA
        usuario_gerencia, created = User.objects.get_or_create(
            username='gerencia_movistar',
            defaults={
                'first_name': 'Gerencia',
                'last_name': 'Movistar',
                'email': 'gerencia@movistar.cl',
                'is_staff': True,  # Acceso al admin
                'is_active': True,
            }
        )
        if created:
            usuario_gerencia.set_password('gerencia1234')
            usuario_gerencia.save()
            usuario_gerencia.groups.add(grupo_gerencia)
            usuarios_creados.append({
                'usuario': 'gerencia_movistar',
                'clave': 'gerencia1234',
                'rol': 'Gerencia',
                'permisos': 'Acceso completo + Admin'
            })
            self.stdout.write(self.style.SUCCESS('OK Usuario "gerencia_movistar" creado'))
        else:
            self.stdout.write(self.style.WARNING('WARNING Usuario "gerencia_movistar" ya existe'))

        # 4. Usuario ADMIN (superusuario)
        usuario_admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'email': 'admin@movistar.cl',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            usuario_admin.set_password('admin1234')
            usuario_admin.save()
            usuarios_creados.append({
                'usuario': 'admin',
                'clave': 'admin1234',
                'rol': 'Administrador',
                'permisos': 'Acceso total al sistema'
            })
            self.stdout.write(self.style.SUCCESS('OK Usuario "admin" (superusuario) creado'))
        else:
            self.stdout.write(self.style.WARNING('WARNING Usuario "admin" ya existe'))

        # Mostrar resumen
        self.stdout.write(self.style.SUCCESS('\n=== USUARIOS CREADOS ===\n'))

        if usuarios_creados:
            self.stdout.write(self.style.SUCCESS('+-------------------------+---------------------+-------------------------------------+'))
            self.stdout.write(self.style.SUCCESS('| USUARIO                 | CONTRASENA          | ROL / PERMISOS                      |'))
            self.stdout.write(self.style.SUCCESS('+-------------------------+---------------------+-------------------------------------+'))

            for u in usuarios_creados:
                usuario_formatted = f"{u['usuario']:<23}"
                clave_formatted = f"{u['clave']:<19}"
                rol_formatted = f"{u['rol']:<15}"
                self.stdout.write(self.style.SUCCESS(
                    f"| {usuario_formatted} | {clave_formatted} | {rol_formatted}             |"
                ))

            self.stdout.write(self.style.SUCCESS('+-------------------------+---------------------+-------------------------------------+'))
        else:
            self.stdout.write(self.style.WARNING('No se crearon usuarios nuevos (ya existian)'))

        self.stdout.write(self.style.SUCCESS('\nOK Proceso completado exitosamente'))
        self.stdout.write(self.style.SUCCESS('\nAccede a: http://localhost:8000/login/'))

    def _asignar_permisos_auditores(self, grupo):
        """Auditores: Mismos permisos que Supervisores"""
        permisos = Permission.objects.filter(
            codename__in=[
                # Ver todo
                'view_tecnico',
                'view_ordentrabajo',
                'view_informemejora',
                'view_imageninformemejora',
                # Modificar órdenes
                'change_ordentrabajo',
                # Crear y modificar informes
                'add_informemejora',
                'change_informemejora',
                'add_imageninformemejora',
                'change_imageninformemejora',
            ]
        )
        grupo.permissions.set(permisos)
        self.stdout.write(self.style.SUCCESS('  -> Permisos de "Auditores" configurados (igual que Supervisores)'))

    def _asignar_permisos_supervisores(self, grupo):
        """Supervisores: Ver todo, crear y modificar informes y órdenes"""
        permisos = Permission.objects.filter(
            codename__in=[
                # Ver todo
                'view_tecnico',
                'view_ordentrabajo',
                'view_informemejora',
                'view_imageninformemejora',
                # Modificar órdenes
                'change_ordentrabajo',
                # Crear y modificar informes
                'add_informemejora',
                'change_informemejora',
                'add_imageninformemejora',
                'change_imageninformemejora',
            ]
        )
        grupo.permissions.set(permisos)
        self.stdout.write(self.style.SUCCESS('  -> Permisos de "Supervisores" configurados'))

    def _asignar_permisos_gerencia(self, grupo):
        """Gerencia: Acceso completo a todo"""
        permisos = Permission.objects.filter(
            content_type__app_label='tecnicos'
        )
        grupo.permissions.set(permisos)
        self.stdout.write(self.style.SUCCESS('  -> Permisos de "Gerencia" configurados (acceso completo)'))
