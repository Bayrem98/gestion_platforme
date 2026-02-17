from datetime import date, datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Poste(models.Model):
    # Ajoutez des choix prédéfinis
    TYPE_POSTE_CHOICES = [
        ('COMPTABLE', 'Comptable'),
        ('RH', 'Ressources Humaines'),
        ('TECHNICIEN', 'Technicien'),
        ('DIRECTEUR', 'Directeur'),
        ('OUVRIER', 'Ouvrier'),
        ('AUTRE', 'Autre'),
    ]
    
    nom = models.CharField(max_length=100, choices=TYPE_POSTE_CHOICES, default='AUTRE')
    autre_nom = models.CharField(max_length=100, blank=True, null=True, verbose_name="Si autre, précisez")
    description = models.TextField(blank=True)
    taux_horaire = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pourcentage_prime = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    def __str__(self):
        if self.nom == 'AUTRE' and self.autre_nom:
            return self.autre_nom
        return self.get_nom_display()

class Employe(models.Model):
    TYPE_CONTRAT_CHOICES = [
        ('CDI', 'CDI'),
        ('CDD', 'CDD'),
        ('INTERIM', 'Intérim'),
        ('STAGE', 'Stage'),
    ]

    POSTE_CHOICES = [
        ('TECHNICIEN', 'Technicien'),
        ('AUTRE', 'Autre (à préciser)'),
    ]
    
    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    cin = models.CharField(max_length=20, unique=True)
    adresse = models.TextField()
    telephone = models.CharField(max_length=20)
    date_naissance = models.DateField()
    date_embauche = models.DateField()
    poste_choice = models.CharField(
        max_length=20, 
        choices=POSTE_CHOICES, 
        default='TECHNICIEN',
        verbose_name="Type de poste"
    )
    poste_autre = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Autre poste (précisez)"
    )
    type_contrat = models.CharField(max_length=20, choices=TYPE_CONTRAT_CHOICES)
    salaire_base = models.DecimalField(max_digits=10, decimal_places=2)
    actif = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='employes/', blank=True, null=True)

    @property
    def poste_display(self):
        """Affiche le poste correctement"""
        if self.poste_choice == 'AUTRE' and self.poste_autre:
            return self.poste_autre
        return self.get_poste_choice_display()
    
    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"

class AvanceSalaire(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_demande = models.DateField(auto_now_add=True)
    date_remboursement = models.DateField(null=True, blank=True)
    rembourse = models.BooleanField(default=False)
    motif = models.TextField()
    
    def __str__(self):
        return f"Avance {self.employe} - {self.montant}TND"

class Freelancer(models.Model):
    TYPE_SERVICE_CHOICES = [
        ('LOGISTIQUE', 'Logistique'),
        ('TRANSPORT', 'Transport'),
        ('AUTRE', 'Autre'),
    ]
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    cin = models.CharField(max_length=20, unique=True)
    adresse = models.TextField()
    telephone = models.CharField(max_length=20)
    email = models.EmailField()
    type_service = models.CharField(max_length=20, choices=TYPE_SERVICE_CHOICES)
    tarif_journalier = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)
    date_inscription = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.type_service}"

class Chantier(models.Model):
    STATUT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('ANNULE', 'Annulé'),
        ('PREVU', 'Prévu'),
    ]
    
    TYPE_CHANTIER_CHOICES = [
        ('CONGRES', 'Congrès'),
        ('FESTIVAL', 'Festival'),
        ('AUTRE', 'Autre'),
    ]
    
    nom = models.CharField(max_length=200)
    type_chantier = models.CharField(max_length=20, choices=TYPE_CHANTIER_CHOICES)
    description = models.TextField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    lieu = models.CharField(max_length=200)
    client_nom = models.CharField(max_length=200)
    client_telephone = models.CharField(max_length=20)
    client_email = models.EmailField()
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='PREVU')
    employes = models.ManyToManyField(Employe, through='AffectationChantier')
    freelancers = models.ManyToManyField(Freelancer, through='AffectationFreelancer')
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.nom} - {self.date_debut}"

class AffectationChantier(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE)
    chantier = models.ForeignKey(Chantier, on_delete=models.CASCADE)
    heures_travaillees = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    date_affectation = models.DateField(auto_now_add=True)
    prime_calculee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def calculer_prime(self):
        if self.employe.poste:
            prime = (self.heures_travaillees * self.employe.poste.taux_horaire * 
                    self.employe.poste.pourcentage_prime / 100)
            return round(prime, 2)
        return 0
    
    def save(self, *args, **kwargs):
        self.prime_calculee = self.calculer_prime()
        super().save(*args, **kwargs)

class AffectationFreelancer(models.Model):
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE)
    chantier = models.ForeignKey(Chantier, on_delete=models.CASCADE)
    jours_travailles = models.IntegerField(default=1)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_affectation = models.DateField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.montant_total = self.freelancer.tarif_journalier * self.jours_travailles
        super().save(*args, **kwargs)

class Prime(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE)
    chantier = models.ForeignKey(Chantier, on_delete=models.CASCADE, null=True, blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_prime = models.DateField(auto_now_add=True)
    mois = models.IntegerField()
    annee = models.IntegerField()
    description = models.TextField()
    payee = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Prime {self.employe} - {self.montant}TND ({self.mois}/{self.annee})"

class Caisse(models.Model):
    nom = models.CharField(max_length=100, default="Caisse Principale")
    solde_actuel = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_derniere_maj = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nom} - {self.solde_actuel}TND"

class Transaction(models.Model):
    TYPE_TRANSACTION_CHOICES = [
        ('RECETTE', 'Recette'),
        ('DEPENSE', 'Dépense'),
    ]
    
    CATEGORIE_CHOICES = [
        ('CLIENT', 'Paiement Client'),
        ('AVANCE', 'Avance sur salaire'),
        ('PRIME', 'Prime employé'),
        ('FREELANCE', 'Paiement Freelancer'),
        ('FOURNITURE', 'Achat fourniture'),
        ('TRANSPORT', 'Frais transport'),
        ('AUTRE', 'Autre'),
    ]
    
    caisse = models.ForeignKey(Caisse, on_delete=models.CASCADE)
    type_transaction = models.CharField(max_length=20, choices=TYPE_TRANSACTION_CHOICES)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_transaction = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)
    chantier = models.ForeignKey(Chantier, on_delete=models.SET_NULL, null=True, blank=True)
    employe = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, blank=True)
    freelancer = models.ForeignKey(Freelancer, on_delete=models.SET_NULL, null=True, blank=True)
    justificatif = models.FileField(upload_to='justificatifs/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.type_transaction} - {self.montant}TND - {self.date_transaction}"
    
    def save(self, *args, **kwargs):
        # Générer la référence UNIQUEMENT si c'est une nouvelle transaction
        if not self.reference:
            # Utiliser la date actuelle
            from django.utils import timezone
            date = self.date_transaction if self.date_transaction else timezone.now()
            
            # Compter les transactions du jour
            today = timezone.now().date()
            count_today = Transaction.objects.filter(
                date_transaction__date=today
            ).count() + 1
            
            self.reference = f"TR-{date.strftime('%Y%m%d')}-{count_today:03d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.type_transaction} - {self.montant}TND - {self.date_transaction.strftime('%d/%m/%Y')}"
    
class Recu(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
    numero_recu = models.CharField(max_length=50, unique=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)  # ← Déjà bon
    beneficiaire = models.CharField(max_length=200)
    motif = models.TextField()
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    imprime = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.numero_recu:
            # Utiliser date_creation ou date du jour
            from django.utils import timezone
            date = self.date_creation if self.date_creation else timezone.now()
            
            last_recu = Recu.objects.order_by('-id').first()
            if last_recu and last_recu.numero_recu:
                try:
                    last_num = int(last_recu.numero_recu.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            self.numero_recu = f"RECU-{date.strftime('%Y%m')}-{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Reçu {self.numero_recu} - {self.beneficiaire}"
    
class PlanningSimple(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='plannings')
    date = models.DateField(verbose_name="Date")
    heure_debut = models.TimeField(verbose_name="Heure de début")
    heure_fin = models.TimeField(verbose_name="Heure de fin")
    notes = models.CharField(max_length=200, blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date', 'heure_debut']
        verbose_name = "Planning"
        verbose_name_plural = "Plannings"
    
    def __str__(self):
        return f"{self.employe} - {self.date} ({self.heure_debut}-{self.heure_fin})"