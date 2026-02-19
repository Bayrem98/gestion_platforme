from datetime import date, datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone
from datetime import date

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
    
    def mettre_a_jour_statut(self):
        """
        Met à jour le statut du chantier en fonction des dates
        """
        today = date.today()
        
        # Ne pas changer le statut si c'est "ANNULE"
        if self.statut == 'ANNULE':
            return self.statut
        
        # Calculer le nouveau statut
        if today > self.date_fin:
            nouveau_statut = 'TERMINE'
        elif self.date_debut <= today <= self.date_fin:
            nouveau_statut = 'EN_COURS'
        else:
            nouveau_statut = 'PREVU'
        
        # Mettre à jour si différent
        if self.statut != nouveau_statut:
            self.statut = nouveau_statut
            self.save(update_fields=['statut'])
        
        return self.statut
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour mettre à jour le statut automatiquement
        """
        # Mettre à jour le statut avant de sauvegarder
        today = date.today()
        
        if not self.pk:  # Nouveau chantier
            if self.statut != 'ANNULE':
                if today > self.date_fin:
                    self.statut = 'TERMINE'
                elif self.date_debut <= today <= self.date_fin:
                    self.statut = 'EN_COURS'
                else:
                    self.statut = 'PREVU'
        else:  # Modification d'un chantier existant
            if self.statut != 'ANNULE':
                if today > self.date_fin:
                    self.statut = 'TERMINE'
                elif self.date_debut <= today <= self.date_fin:
                    self.statut = 'EN_COURS'
                else:
                    self.statut = 'PREVU'
        
        super().save(*args, **kwargs)
    
    @property
    def statut_couleur(self):
        """
        Retourne la couleur Bootstrap pour chaque statut
        """
        couleurs = {
            'PREVU': 'warning',
            'EN_COURS': 'success',
            'TERMINE': 'secondary',
            'ANNULE': 'danger',
        }
        return couleurs.get(self.statut, 'info')
    
    @property
    def jours_restants(self):
        """
        Calcule le nombre de jours restants avant la fin
        """
        today = date.today()
        if today > self.date_fin:
            return 0
        return (self.date_fin - today).days
    
    @property
    def progression(self):
        """
        Calcule le pourcentage de progression du chantier
        """
        total_jours = (self.date_fin - self.date_debut).days
        if total_jours <= 0:
            return 100 if self.statut == 'TERMINE' else 0
        
        jours_ecoules = (date.today() - self.date_debut).days
        if jours_ecoules < 0:
            return 0
        elif jours_ecoules > total_jours:
            return 100
        else:
            return int((jours_ecoules / total_jours) * 100)
    
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

class Notification(models.Model):
    TYPE_CHOICES = [
        ('INFO', 'Information'),
        ('SUCCESS', 'Succès'),
        ('WARNING', 'Avertissement'),
        ('DANGER', 'Important'),
    ]
    
    CATEGORIE_CHOICES = [
        ('EMPLOYE', 'Employé'),
        ('FREELANCER', 'Freelancer'),
        ('CHANTIER', 'Chantier'),
        ('TRANSACTION', 'Transaction'),
        ('PRIME', 'Prime'),
        ('PLANNING', 'Planning'),
        ('SYSTEME', 'Système'),
    ]
    
    titre = models.CharField(max_length=200)
    message = models.TextField()
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES, default='INFO')
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='SYSTEME')
    lien = models.CharField(max_length=200, blank=True, null=True, help_text="Lien vers la ressource concernée")
    est_lu = models.BooleanField(default=False)
    est_archive = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_lecture = models.DateTimeField(null=True, blank=True)
    
    # Pour lier à des objets spécifiques
    employe = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, blank=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    chantier = models.ForeignKey(Chantier, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} - {self.date_creation.strftime('%d/%m/%Y %H:%M')}"
    
    def marquer_comme_lu(self):
        from django.utils import timezone
        self.est_lu = True
        self.date_lecture = timezone.now()
        self.save()    

class Facture(models.Model):
    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('ENVOYEE', 'Envoyée'),
        ('PAYEE', 'Payée'),
        ('EN_RETARD', 'En retard'),
        ('ANNULEE', 'Annulée'),
    ]
    
    MODE_PAIEMENT_CHOICES = [
        ('ESPECES', 'Espèces'),
        ('CHEQUE', 'Chèque'),
        ('VIREMENT', 'Virement bancaire'),
        ('CARTE', 'Carte bancaire'),
        ('AUTRE', 'Autre'),
    ]
    
    numero_facture = models.CharField(max_length=50, unique=True, blank=True)
    chantier = models.ForeignKey(Chantier, on_delete=models.CASCADE, related_name='factures')
    date_emission = models.DateField(auto_now_add=True)  # ← Ce champ est automatique
    date_echeance = models.DateField()
    date_paiement = models.DateField(null=True, blank=True)
    
    # Montants
    montant_ht = models.DecimalField(max_digits=12, decimal_places=2)
    tva = models.DecimalField(max_digits=5, decimal_places=2, default=20.0)
    montant_ttc = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Détails
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='BROUILLON')
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, null=True, blank=True)
    
    # Informations client (au moment de la facture)
    client_nom = models.CharField(max_length=200)
    client_adresse = models.TextField()
    client_telephone = models.CharField(max_length=20)
    client_email = models.EmailField()
    
    # Informations société
    societe_nom = models.CharField(max_length=200, default="STAGE PROD")
    societe_adresse = models.TextField(default="123 Rue de l'Entreprise, 75000 Paris")
    societe_telephone = models.CharField(max_length=20, default="01 23 45 67 89")
    societe_email = models.EmailField(default="contact@stageprod.fr")
    societe_siret = models.CharField(max_length=20, default="123 456 789 00012")
    
    # Documents
    fichier_pdf = models.FileField(upload_to='factures/', blank=True, null=True)
    
    # Métadonnées
    notes = models.TextField(blank=True, null=True)
    conditions = models.TextField(default="Paiement à réception sous 30 jours")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_emission']
    
    def save(self, *args, **kwargs):
        # Calculer le TTC si non défini
        if not self.montant_ttc:
            self.montant_ttc = self.montant_ht * (1 + self.tva / 100)
        
        # Générer le numéro de facture SEULEMENT si c'est une nouvelle facture
        if not self.numero_facture:
            from django.utils import timezone
            # Utiliser la date actuelle si date_emission n'est pas encore définie
            date = self.date_emission if self.date_emission else timezone.now().date()
            annee = date.year
            
            # Compter les factures de l'année
            last_facture = Facture.objects.filter(
                date_emission__year=annee
            ).order_by('-id').first()
            
            if last_facture and last_facture.numero_facture:
                try:
                    last_num = int(last_facture.numero_facture.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError, AttributeError):
                    new_num = 1
            else:
                new_num = 1
            
            self.numero_facture = f"FAC-{annee}-{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def jours_retard(self):
        """Calcule le nombre de jours de retard"""
        from datetime import date
        if self.statut == 'PAYEE':
            return 0
        today = date.today()
        if today > self.date_echeance:
            return (today - self.date_echeance).days
        return 0
    
    @property
    def statut_couleur(self):
        couleurs = {
            'BROUILLON': 'secondary',
            'ENVOYEE': 'info',
            'PAYEE': 'success',
            'EN_RETARD': 'danger',
            'ANNULEE': 'dark',
        }
        return couleurs.get(self.statut, 'secondary')
    
    def __str__(self):
        return f"{self.numero_facture} - {self.chantier.nom}"

class LigneFacture(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    description = models.CharField(max_length=255)
    quantite = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.montant = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.description} - {self.montant}TND"