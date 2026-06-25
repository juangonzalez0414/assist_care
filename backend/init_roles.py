import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Rol

def init_roles():
    roles = ['Persona que necesita ayuda', 'Acompañante', 'Administrador']
    for nombre in roles:
        rol, created = Rol.objects.get_or_create(nombre_rol=nombre)
        if created:
            print(f"Rol creado: {nombre}")
        else:
            print(f"Rol ya existía: {nombre}")

if __name__ == "__main__":
    init_roles()
