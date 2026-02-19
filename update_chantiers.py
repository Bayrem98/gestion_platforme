import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'platforme.settings')
django.setup()

from gestion.models import Chantier

def update_all_chantiers():
    """Met à jour tous les chantiers"""
    print(f"\n{'='*50}")
    print(f"MISE À JOUR DES CHANTIERS - {date.today()}")
    print(f"{'='*50}\n")
    
    chantiers = Chantier.objects.all()
    count = 0
    
    for chantier in chantiers:
        ancien = chantier.statut
        nouveau = chantier.mettre_a_jour_statut()
        
        if ancien != nouveau:
            count += 1
            print(f"✓ {chantier.nom[:30]:30} : {ancien:8} → {nouveau:8}")
    
    if count == 0:
        print("Aucun changement de statut")
    
    print(f"\n✅ {count} chantier(s) mis à jour")
    print(f"📊 Total: {chantiers.count()} chantiers")

if __name__ == "__main__":
    update_all_chantiers()