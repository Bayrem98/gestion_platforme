from django.core.management.base import BaseCommand
from gestion.models import Chantier
from datetime import date

class Command(BaseCommand):
    help = 'Met à jour le statut de tous les chantiers'

    def handle(self, *args, **options):
        chantiers = Chantier.objects.all()
        count = 0
        
        for chantier in chantiers:
            ancien_statut = chantier.statut
            nouveau_statut = chantier.mettre_a_jour_statut()
            
            if ancien_statut != nouveau_statut:
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Chantier "{chantier.nom}" : {ancien_statut} → {nouveau_statut}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ {count} chantier(s) mis à jour')
        )