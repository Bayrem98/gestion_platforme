from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Crée un superutilisateur par défaut si aucun n\'existe'

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            username = os.environ.get('ADMIN_USERNAME', 'admin')
            email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            password = os.environ.get('ADMIN_PASSWORD', 'Admin123!')
            
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'Superutilisateur "{username}" créé avec succès'))
        else:
            self.stdout.write('Un superutilisateur existe déjà')