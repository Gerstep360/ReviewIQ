"""Servidor de desarrollo para endpoints que no usan base de datos."""

from django.contrib.staticfiles.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    help = 'Sirve la API sin comprobar migraciones; no usar admin ni funciones con base de datos.'

    def check_migrations(self):
        # Se conservan los demás checks, el servidor Django y los estáticos de Swagger.
        # runserver y migrate siguen usando PostgreSQL normalmente.
        self.stdout.write('API sin persistencia: se omite la comprobación de migraciones.\n')
