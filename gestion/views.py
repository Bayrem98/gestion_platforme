from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from .models import *
from .forms import *
from datetime import datetime, timedelta, date
from decimal import Decimal
from .forms import RecuForm
from calendar import monthcalendar, day_name
from .models import PlanningSimple
from .forms import PlanningSimpleForm
from .utils import *
from django.http import JsonResponse
from django.utils import timezone
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from datetime import datetime

@login_required
def dashboard(request):
    try:
        context = {
            'total_employes': Employe.objects.filter(actif=True).count(),
            'total_freelancers': Freelancer.objects.filter(disponible=True).count(),
            'chantiers_actifs': Chantier.objects.filter(statut='EN_COURS').count(),
            'caisse': Caisse.objects.first(),
            'dernieres_transactions': Transaction.objects.order_by('-date_transaction')[:10],
            'employes_recents': Employe.objects.order_by('-date_embauche')[:5],
            'chantiers_recents': Chantier.objects.order_by('-date_debut')[:5],
        }
        return render(request, 'dashboard.html', context)
    except Exception as e:
        print(f"Erreur dashboard: {e}")
        return render(request, 'dashboard.html', {'error': str(e)})

# Employees Views
@login_required
def liste_employes(request):
    employes = Employe.objects.all()
    poste_filter = request.GET.get('poste')
    actif_filter = request.GET.get('actif')
    
    if poste_filter:
        employes = employes.filter(poste_id=poste_filter)
    if actif_filter:
        employes = employes.filter(actif=(actif_filter == 'true'))
    
    context = {
        'employes': employes,
        'postes': Poste.objects.all(),
    }
    return render(request, 'employees/liste_employes.html', context)

@login_required
def ajouter_employe(request):
    """Ajouter un nouvel employé"""
    if request.method == 'POST':
        form = EmployeForm(request.POST, request.FILES)
        if form.is_valid():
            employe = form.save()
            notifier_nouvel_employe(employe)
            messages.success(request, f'Employé {employe.nom} {employe.prenom} ajouté avec succès!')
            return redirect('liste_employes')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = EmployeForm()
    
    return render(request, 'employees/ajouter_employe.html', {'form': form})

@login_required
def detail_employe(request, pk):
    """Détail d'un employé"""
    employe = get_object_or_404(Employe, pk=pk)
    avances = AvanceSalaire.objects.filter(employe=employe).order_by('-date_demande')
    primes = Prime.objects.filter(employe=employe).order_by('-date_prime')
    chantiers = AffectationChantier.objects.filter(employe=employe).select_related('chantier')
    
    # Debug - à supprimer après vérification
    print(f"Employé: {employe.nom} {employe.prenom}")
    print(f"poste_choice: {employe.poste_choice}")
    print(f"poste_autre: {employe.poste_autre}")
    
    context = {
        'employe': employe,
        'avances': avances,
        'primes': primes,
        'chantiers': chantiers,
    }
    return render(request, 'employees/detail_employe.html', context)

@login_required
def ajouter_avance(request, pk):
    """Ajouter une avance sur salaire"""
    employe = get_object_or_404(Employe, pk=pk)
    
    if request.method == 'POST':
        montant = request.POST.get('montant')
        motif = request.POST.get('motif')
        
        # 1. Créer l'avance
        avance = AvanceSalaire.objects.create(
            employe=employe,
            montant=montant,
            motif=motif
        )
        
        # 2. Créer la transaction pour la caisse
        caisse = Caisse.objects.first()
        if not caisse:
            caisse = Caisse.objects.create(nom="Caisse Principale", solde_actuel=0)
        
        # Créer la transaction - la date sera automatique !
        transaction = Transaction.objects.create(
            caisse=caisse,
            type_transaction='DEPENSE',
            categorie='AVANCE',
            montant=montant,
            description=f"Avance sur salaire - {employe.nom} {employe.prenom} - {motif[:50]}",
            employe=employe
        )
        
        # 3. Mettre à jour le solde de la caisse
        caisse.solde_actuel -= Decimal(montant)
        caisse.save()
        notifier_avance_salaire(avance)
        
        messages.success(request, f'Avance sur salaire de {montant}TND enregistrée !')
        return redirect('detail_employe', pk=pk)
    
    return render(request, 'employees/ajouter_avance.html', {'employe': employe})

# Chantiers Views
@login_required
def liste_chantiers(request):
    """
    Liste des chantiers avec mise à jour automatique des statuts
    """
    # Mettre à jour tous les statuts avant d'afficher la liste
    chantiers = Chantier.objects.all()
    for chantier in chantiers:
        chantier.mettre_a_jour_statut()
    
    # Filtrer selon les paramètres
    statut_filter = request.GET.get('statut')
    type_filter = request.GET.get('type')
    
    if statut_filter:
        chantiers = chantiers.filter(statut=statut_filter)
    if type_filter:
        chantiers = chantiers.filter(type_chantier=type_filter)
    
    context = {
        'chantiers': chantiers,
        'statuts': Chantier.STATUT_CHOICES,
        'types': Chantier.TYPE_CHANTIER_CHOICES,
        'today': date.today(),
    }
    return render(request, 'chantiers/liste_chantiers.html', context)

@login_required
def detail_chantier(request, pk):
    """Détail d'un chantier avec statut mis à jour"""
    chantier = get_object_or_404(Chantier, pk=pk)
    
    # Mettre à jour le statut avant d'afficher
    chantier.mettre_a_jour_statut()
    
    affectations_employes = AffectationChantier.objects.filter(chantier=chantier)
    affectations_freelancers = AffectationFreelancer.objects.filter(chantier=chantier)
    transactions = Transaction.objects.filter(chantier=chantier)
    
    context = {
        'chantier': chantier,
        'affectations_employes': affectations_employes,
        'affectations_freelancers': affectations_freelancers,
        'transactions': transactions,
        'aujourdhui': date.today(),
    }
    return render(request, 'chantiers/detail_chantier.html', context)

@login_required
def affecter_employe(request, pk):
    chantier = get_object_or_404(Chantier, pk=pk)
    
    if request.method == 'POST':
        form = AffectationChantierForm(request.POST)
        if form.is_valid():
            affectation = form.save(commit=False)
            affectation.chantier = chantier
            affectation.save()
            messages.success(request, 'Employé affecté au chantier!')
            return redirect('detail_chantier', pk=pk)
    else:
        form = AffectationChantierForm()
        form.fields['employe'].queryset = Employe.objects.filter(actif=True)
    
    return render(request, 'chantiers/affecter_employe.html', {
        'form': form,
        'chantier': chantier
    })

# Primes Views
@login_required
def calculer_primes(request):
    if request.method == 'POST':
        mois = int(request.POST.get('mois'))
        annee = int(request.POST.get('annee'))
        
        affectations = AffectationChantier.objects.filter(
            chantier__statut='TERMINE',
            date_affectation__month=mois,
            date_affectation__year=annee
        )
        
        primes_creees = 0
        for affectation in affectations:
            if affectation.prime_calculee > 0:
                prime, created = Prime.objects.get_or_create(
                    employe=affectation.employe,
                    chantier=affectation.chantier,
                    mois=mois,
                    annee=annee,
                    defaults={
                        'montant': affectation.prime_calculee,
                        'description': f"Prime automatique - Chantier: {affectation.chantier.nom}"
                    }
                )
                if created:
                    primes_creees += 1
        
        messages.success(request, f'{primes_creees} primes calculées avec succès!')
        return redirect('liste_primes')
    
    return render(request, 'primes/calculer_primes.html')

# Finance Views
@login_required
def finance_dashboard(request):
    caisse = Caisse.objects.first()
    if not caisse:
        caisse = Caisse.objects.create(solde_actuel=0)
    
    aujourd_hui = date.today()
    premier_jour_mois = aujourd_hui.replace(day=1)
    
    transactions_mois = Transaction.objects.filter(date_transaction__date__gte=premier_jour_mois)
    
    recettes_mois = transactions_mois.filter(type_transaction='RECETTE').aggregate(Sum('montant'))['montant__sum'] or 0
    depenses_mois = transactions_mois.filter(type_transaction='DEPENSE').aggregate(Sum('montant'))['montant__sum'] or 0
    
    context = {
        'caisse': caisse,
        'recettes_mois': recettes_mois,
        'depenses_mois': depenses_mois,
        'solde_mois': recettes_mois - depenses_mois,
        'dernieres_transactions': Transaction.objects.order_by('-date_transaction')[:20],
    }
    return render(request, 'finance/dashboard.html', context)

@login_required
def ajouter_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save()
            notifier_nouvelle_transaction(transaction)
            # Mettre à jour le solde de la caisse
            caisse = transaction.caisse
            if transaction.type_transaction == 'RECETTE':
                caisse.solde_actuel += transaction.montant
            else:
                caisse.solde_actuel -= transaction.montant
            caisse.save()
            
            # Créer un reçu si nécessaire
            if transaction.type_transaction == 'DEPENSE':
                recu = Recu.objects.create(
                    transaction=transaction,
                    beneficiaire=transaction.employe or transaction.freelancer or "Bénéficiaire inconnu",
                    motif=transaction.description
                )
            
            messages.success(request, 'Transaction enregistrée avec succès!')
            return redirect('finance_dashboard')
    else:
        form = TransactionForm()
        form.fields['caisse'].initial = Caisse.objects.first()
    
    return render(request, 'finance/ajouter_transaction.html', {'form': form})

@login_required
def generer_recu(request, pk):
    """Générer un reçu pour une transaction avec formulaire"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    # Vérifier si un reçu existe déjà
    try:
        recu = Recu.objects.get(transaction=transaction)
        # Si le reçu existe, rediriger vers l'impression
        return redirect('imprimer_recu', pk=recu.pk)
    except Recu.DoesNotExist:
        recu = None
    
    if request.method == 'POST':
        form = RecuForm(request.POST)
        if form.is_valid():
            # Créer le reçu avec les données du formulaire
            recu = form.save(commit=False)
            recu.transaction = transaction
            recu.save()  # Maintenant ça fonctionne !
            messages.success(request, 'Reçu généré avec succès!')
            return redirect('imprimer_recu', pk=recu.pk)
    else:
        # Pré-remplir le formulaire si possible
        initial_data = {}
        if transaction.employe:
            initial_data['beneficiaire'] = f"{transaction.employe.nom} {transaction.employe.prenom}"
        elif transaction.freelancer:
            initial_data['beneficiaire'] = f"{transaction.freelancer.nom} {transaction.freelancer.prenom}"
        
        initial_data['motif'] = transaction.description
        form = RecuForm(initial=initial_data)
    
    context = {
        'form': form,
        'transaction': transaction,
    }
    return render(request, 'finance/generer_recu.html', context)

@login_required
def imprimer_recu(request, pk):
    """Afficher le reçu pour impression"""
    recu = get_object_or_404(Recu, pk=pk)
    recu.imprime = True
    recu.save()
    
    transaction = recu.transaction
    
    context = {
        'recu': recu,
        'transaction': transaction,
        'entreprise': {
            'nom': 'Votre Société',
            'adresse': '123 Rue de l\'Entreprise, 75000 Paris',
            'telephone': '01 23 45 67 89',
            'email': 'contact@votre-societe.com',
            'siret': '123 456 789 00012',
            'capital': '10 000 TND'
        }
    }
    return render(request, 'finance/imprimer_recu.html', context)

@login_required
def modifier_employe(request, pk):
    """Modifier un employé existant"""
    employe = get_object_or_404(Employe, pk=pk)
    
    if request.method == 'POST':
        form = EmployeForm(request.POST, request.FILES, instance=employe)
        if form.is_valid():
            form.save()
            messages.success(request, f'Employé {employe.nom} {employe.prenom} modifié avec succès!')
            return redirect('detail_employe', pk=employe.pk)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = EmployeForm(instance=employe)
        
        # Debug : voir les valeurs
        print("=== DEBUG MODIFICATION ===")
        print(f"Employé: {employe.nom} {employe.prenom}")
        print(f"Date naissance: {employe.date_naissance}")
        print(f"Date embauche: {employe.date_embauche}")
        print(f"Valeur initiale date naissance: {form.initial.get('date_naissance')}")
        print(f"Valeur initiale date embauche: {form.initial.get('date_embauche')}")
    
    return render(request, 'employees/modifier_employe.html', {
        'form': form,
        'employe': employe
    })

@login_required
def supprimer_employe(request, pk):
    """Supprimer un employé avec confirmation"""
    employe = get_object_or_404(Employe, pk=pk)
    
    if request.method == 'POST':
        # Sauvegarder les infos pour le message
        nom_complet = f"{employe.nom} {employe.prenom}"
        matricule = employe.matricule
        
        # Supprimer l'employé
        employe.delete()
        
        # Message de succès
        messages.success(request, f'Employé {nom_complet} (Matricule: {matricule}) supprimé avec succès!')
        return redirect('liste_employes')
    
    return render(request, 'employees/supprimer_employe.html', {'employe': employe})

@login_required
def ajouter_freelancer(request):
    """Ajouter un nouveau freelancer"""
    if request.method == 'POST':
        form = FreelancerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Freelancer ajouté avec succès!')
            return redirect('liste_freelancers')
    else:
        form = FreelancerForm()
    
    return render(request, 'freelancers/ajouter_freelancer.html', {'form': form})

@login_required
def liste_freelancers(request):
    """Liste des freelancers"""
    freelancers = Freelancer.objects.all()
    return render(request, 'freelancers/liste_freelancers.html', {'freelancers': freelancers})

@login_required
def detail_freelancer(request, pk):
    """Détail d'un freelancer"""
    freelancer = get_object_or_404(Freelancer, pk=pk)
    affectations = AffectationFreelancer.objects.filter(freelancer=freelancer)
    return render(request, 'freelancers/detail_freelancer.html', {
        'freelancer': freelancer,
        'affectations': affectations
    })

@login_required
def modifier_freelancer(request, pk):
    """Modifier un freelancer"""
    freelancer = get_object_or_404(Freelancer, pk=pk)
    if request.method == 'POST':
        form = FreelancerForm(request.POST, instance=freelancer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Freelancer modifié avec succès!')
            return redirect('detail_freelancer', pk=pk)
    else:
        form = FreelancerForm(instance=freelancer)
    
    return render(request, 'freelancers/modifier_freelancer.html', {
        'form': form,
        'freelancer': freelancer
    })

@login_required
def ajouter_chantier(request):
    """Ajouter un nouveau chantier"""
    if request.method == 'POST':
        form = ChantierForm(request.POST)
        if form.is_valid():
            chantier = form.save()
            notifier_nouveau_chantier(chantier)
            messages.success(request, 'Chantier ajouté avec succès!')
            return redirect('liste_chantiers')
    else:
        form = ChantierForm()
    
    return render(request, 'chantiers/ajouter_chantier.html', {'form': form})

@login_required
def affecter_freelancer(request, pk):
    """Affecter un freelancer à un chantier"""
    chantier = get_object_or_404(Chantier, pk=pk)
    
    if request.method == 'POST':
        freelancer_id = request.POST.get('freelancer')
        jours = request.POST.get('jours_travailles', 1)
        
        freelancer = get_object_or_404(Freelancer, pk=freelancer_id)
        
        affectation = AffectationFreelancer.objects.create(
            freelancer=freelancer,
            chantier=chantier,
            jours_travailles=jours
        )
        
        messages.success(request, f'{freelancer.nom} {freelancer.prenom} affecté au chantier!')
        return redirect('detail_chantier', pk=pk)
    
    freelancers = Freelancer.objects.filter(disponible=True)
    return render(request, 'chantiers/affecter_freelancer.html', {
        'chantier': chantier,
        'freelancers': freelancers
    })

@login_required
def liste_primes(request):
    """Liste des primes"""
    primes = Prime.objects.all().order_by('-annee', '-mois', 'employe__nom')
    return render(request, 'primes/liste_primes.html', {'primes': primes})

@login_required
def ajouter_prime(request):
    """Ajouter une prime manuellement"""
    if request.method == 'POST':
        form = PrimeForm(request.POST)
        if form.is_valid():
            prime = form.save()
            notifier_prime_calculee(prime)
            messages.success(request, 'Prime ajoutée avec succès!')
            return redirect('liste_primes')
    else:
        form = PrimeForm()
    
    return render(request, 'primes/ajouter_prime.html', {'form': form})

@login_required
def payer_prime(request, pk):
    """Marquer une prime comme payée"""
    prime = get_object_or_404(Prime, pk=pk)
    prime.payee = True
    prime.save()
    
    # Créer une transaction dans la caisse
    caisse = Caisse.objects.first()
    if caisse:
        Transaction.objects.create(
            caisse=caisse,
            type_transaction='DEPENSE',
            categorie='PRIME',
            montant=prime.montant,
            description=f"Prime - {prime.employe.nom} {prime.employe.prenom} ({prime.mois}/{prime.annee})",
            employe=prime.employe,
            chantier=prime.chantier
        )
        caisse.solde_actuel -= prime.montant
        caisse.save()
    
    messages.success(request, 'Prime marquée comme payée!')
    return redirect('liste_primes')

@login_required
def liste_transactions(request):
    """Liste de toutes les transactions"""
    transactions = Transaction.objects.all().order_by('-date_transaction')
    return render(request, 'finance/liste_transactions.html', {'transactions': transactions})

@login_required
def planning_simple(request, pk):
    """Planning mensuel simple avec calendrier"""
    employe = get_object_or_404(Employe, pk=pk)
    
    # Mois sélectionné (par défaut le mois courant)
    today = datetime.now()
    annee = int(request.GET.get('annee', today.year))
    mois = int(request.GET.get('mois', today.month))
    
    print(f"=== DEBUG PLANNING ===")  # Pour déboguer
    print(f"Employé: {employe.nom} {employe.prenom}")
    print(f"Mois affiché: {mois}/{annee}")
    
    # Créer le calendrier du mois
    cal = monthcalendar(annee, mois)
    
    # Récupérer les plannings du mois
    plannings = PlanningSimple.objects.filter(
        employe=employe,
        date__year=annee,
        date__month=mois
    ).order_by('date', 'heure_debut')
    
    print(f"Nombre de plannings trouvés: {plannings.count()}")
    
    # Organiser par date
    plannings_par_date = {}
    for p in plannings:
        date_str = p.date.strftime('%Y-%m-%d')
        if date_str not in plannings_par_date:
            plannings_par_date[date_str] = []
        plannings_par_date[date_str].append(p)
        print(f"Planning ajouté: {date_str} - {p.heure_debut}-{p.heure_fin}")
    
    # Noms des jours en français
    jours_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    
    # Mois en français
    mois_fr = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 
               'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    
    # Calcul des mois précédent/suivant
    if mois == 1:
        mois_precedent = 12
        annee_precedente = annee - 1
    else:
        mois_precedent = mois - 1
        annee_precedente = annee
        
    if mois == 12:
        mois_suivant = 1
        annee_suivante = annee + 1
    else:
        mois_suivant = mois + 1
        annee_suivante = annee
    
    context = {
        'employe': employe,
        'calendrier': cal,
        'plannings_par_date': plannings_par_date,
        'mois': mois,
        'annee': annee,
        'mois_nom': mois_fr[mois-1],
        'jours_fr': jours_fr,
        'mois_precedent': mois_precedent,
        'annee_precedente': annee_precedente,
        'mois_suivant': mois_suivant,
        'annee_suivante': annee_suivante,
        'today': today,
    }
    return render(request, 'employees/planning_simple.html', context)

@login_required
def ajouter_planning_simple(request, pk):
    """Ajouter un horaire pour un employé"""
    employe = get_object_or_404(Employe, pk=pk)
    
    if request.method == 'POST':
        form = PlanningSimpleForm(request.POST)
        if form.is_valid():
            planning = form.save(commit=False)
            planning.employe = employe
            planning.save()
            notifier_nouveau_planning(planning)
            messages.success(request, f'✅ Horaire ajouté pour le {planning.date.strftime("%d/%m/%Y")}')
            
            # Rediriger vers le planning avec le même mois que la date ajoutée
            return redirect(f"{reverse('planning_simple', args=[employe.pk])}?annee={planning.date.year}&mois={planning.date.month}")
        else:
            messages.error(request, '❌ Erreur dans le formulaire. Veuillez vérifier les champs.')
    else:
        # Date pré-remplie si fournie dans l'URL
        date_defaut = request.GET.get('date')
        if date_defaut:
            try:
                date_defaut = datetime.strptime(date_defaut, '%Y-%m-%d').date()
            except:
                date_defaut = datetime.now().date()
        else:
            date_defaut = datetime.now().date()
        
        form = PlanningSimpleForm(initial={'date': date_defaut})
    
    return render(request, 'employees/ajouter_planning_simple.html', {
        'form': form,
        'employe': employe
    })

@login_required
def modifier_planning_simple(request, pk):
    """Modifier un horaire"""
    planning = get_object_or_404(PlanningSimple, pk=pk)
    
    if request.method == 'POST':
        form = PlanningSimpleForm(request.POST, instance=planning)
        if form.is_valid():
            form.save()
            messages.success(request, f'Horaire du {planning.date.strftime("%d/%m/%Y")} modifié avec succès')
            return redirect('planning_simple', pk=planning.employe.pk)  # ← Redirection vers le planning
        else:
            messages.error(request, 'Erreur dans le formulaire.')
    else:
        form = PlanningSimpleForm(instance=planning)
    
    return render(request, 'employees/modifier_planning_simple.html', {
        'form': form,
        'planning': planning,
        'employe': planning.employe
    })

@login_required
def supprimer_planning_simple(request, pk):
    """Supprimer un horaire"""
    planning = get_object_or_404(PlanningSimple, pk=pk)
    employe_pk = planning.employe.pk
    date_str = planning.date.strftime("%d/%m/%Y")
    
    if request.method == 'POST':
        planning.delete()
        messages.success(request, f'Horaire du {date_str} supprimé avec succès')
        return redirect('planning_simple', pk=employe_pk)  # ← Redirection vers le planning
    
    return render(request, 'employees/supprimer_planning_simple.html', {
        'planning': planning
    })

@login_required
def test_planning(request, pk):
    """Vue de test pour vérifier les plannings"""
    employe = get_object_or_404(Employe, pk=pk)
    plannings = PlanningSimple.objects.filter(employe=employe).order_by('-date')
    
    html = "<h1>Plannings pour " + str(employe) + "</h1>"
    html += "<table border='1'><tr><th>ID</th><th>Date</th><th>Heure début</th><th>Heure fin</th><th>Notes</th></tr>"
    
    for p in plannings:
        html += f"<tr><td>{p.id}</td><td>{p.date}</td><td>{p.heure_debut}</td><td>{p.heure_fin}</td><td>{p.notes}</td></tr>"
    
    html += "</table>"
    return HttpResponse(html)

@login_required
def get_notifications(request):
    """API pour récupérer les notifications (AJAX)"""
    # Récupérer les notifications non lues
    notifications = Notification.objects.filter(est_lu=False, est_archive=False)[:10]
    
    # Compter le total non lu
    non_lu_count = Notification.objects.filter(est_lu=False, est_archive=False).count()
    
    data = {
        'count': non_lu_count,
        'notifications': [
            {
                'id': n.id,
                'titre': n.titre,
                'message': n.message,
                'type': n.type_notification,
                'categorie': n.categorie,
                'date': n.date_creation.strftime('%d/%m/%Y %H:%M'),
                'lien': n.lien,
                'icone': get_notification_icon(n.categorie, n.type_notification),
                'time_ago': get_time_ago(n.date_creation)
            }
            for n in notifications
        ]
    }
    return JsonResponse(data)

@login_required
def marquer_notification_lue(request, pk):
    """Marquer une notification comme lue"""
    try:
        notification = Notification.objects.get(pk=pk)
        notification.marquer_comme_lu()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification non trouvée'}, status=404)

@login_required
def marquer_tout_lu(request):
    """Marquer toutes les notifications comme lues"""
    Notification.objects.filter(est_lu=False).update(
        est_lu=True,
        date_lecture=timezone.now()
    )
    return JsonResponse({'status': 'success'})

@login_required
def liste_notifications(request):
    """Page de toutes les notifications"""
    notifications = Notification.objects.filter(est_archive=False).order_by('-date_creation')
    return render(request, 'notifications/liste.html', {'notifications': notifications})

def get_notification_icon(categorie, type_notif):
    """Retourne l'icône Font Awesome pour une notification"""
    icons = {
        'EMPLOYE': 'fas fa-user',
        'FREELANCER': 'fas fa-user-tie',
        'CHANTIER': 'fas fa-hard-hat',
        'TRANSACTION': 'fas fa-euro-sign',
        'PRIME': 'fas fa-gift',
        'PLANNING': 'fas fa-calendar-alt',
        'SYSTEME': 'fas fa-cog',
    }
    
    colors = {
        'SUCCESS': 'success',
        'WARNING': 'warning',
        'DANGER': 'danger',
        'INFO': 'info',
    }
    
    return {
        'icon': icons.get(categorie, 'fas fa-bell'),
        'color': colors.get(type_notif, 'info')
    }

def get_time_ago(date):
    """Retourne le temps écoulé en français"""
    from django.utils import timezone
    now = timezone.now()
    diff = now - date
    
    if diff.days > 0:
        return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
    elif diff.seconds >= 3600:
        heures = diff.seconds // 3600
        return f"Il y a {heures} heure{'s' if heures > 1 else ''}"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
    else:
        return "À l'instant"

@login_required
def liste_factures_chantier(request, pk):
    """Liste des factures d'un chantier"""
    chantier = get_object_or_404(Chantier, pk=pk)
    factures = Facture.objects.filter(chantier=chantier).order_by('-date_emission')
    
    context = {
        'chantier': chantier,
        'factures': factures,
    }
    return render(request, 'chantiers/liste_factures.html', context)

@login_required
def creer_facture(request, pk):
    """Créer une nouvelle facture pour un chantier"""
    chantier = get_object_or_404(Chantier, pk=pk)
    
    if request.method == 'POST':
        form = FactureForm(request.POST)
        if form.is_valid():
            facture = form.save(commit=False)
            facture.chantier = chantier
            facture.client_nom = chantier.client_nom
            facture.client_telephone = chantier.client_telephone
            facture.client_email = chantier.client_email
            facture.client_adresse = chantier.lieu
            # Le montant TTC sera calculé dans le modèle
            facture.save()
            
            messages.success(request, f'Facture {facture.numero_facture} créée avec succès')
            return redirect('detail_facture', pk=facture.pk)
        else:
            messages.error(request, 'Erreur dans le formulaire. Veuillez vérifier les champs.')
    else:
        # Pré-remplir avec les données du chantier
        initial_data = {
            'montant_ht': chantier.montant_total,
            'client_nom': chantier.client_nom,
            'client_telephone': chantier.client_telephone,
            'client_email': chantier.client_email,
            'client_adresse': chantier.lieu,
            'date_echeance': date.today() + timedelta(days=30),  # Échéance à 30 jours
        }
        form = FactureForm(initial=initial_data)
    
    context = {
        'form': form,
        'chantier': chantier,
    }
    return render(request, 'chantiers/creer_facture.html', context)

@login_required
def detail_facture(request, pk):
    """Détail d'une facture"""
    facture = get_object_or_404(Facture, pk=pk)
    
    context = {
        'facture': facture,
        'chantier': facture.chantier,
    }
    return render(request, 'chantiers/detail_facture.html', context)

@login_required
def modifier_facture(request, pk):
    """Modifier une facture"""
    facture = get_object_or_404(Facture, pk=pk)
    
    if request.method == 'POST':
        form = FactureForm(request.POST, instance=facture)
        if form.is_valid():
            form.save()
            messages.success(request, 'Facture modifiée avec succès')
            return redirect('detail_facture', pk=facture.pk)
    else:
        form = FactureForm(instance=facture)
    
    context = {
        'form': form,
        'facture': facture,
    }
    return render(request, 'chantiers/modifier_facture.html', context)

@login_required
def ajouter_ligne_facture(request, pk):
    """Ajouter une ligne à une facture"""
    facture = get_object_or_404(Facture, pk=pk)
    
    if request.method == 'POST':
        form = LigneFactureForm(request.POST)
        if form.is_valid():
            ligne = form.save(commit=False)
            ligne.facture = facture
            ligne.save()
            
            # Mettre à jour le montant total de la facture
            total = facture.lignes.aggregate(total=models.Sum('montant'))['total'] or 0
            facture.montant_ht = total
            facture.montant_ttc = total * (1 + facture.tva / 100)
            facture.save()
            
            messages.success(request, 'Ligne ajoutée avec succès')
            return redirect('detail_facture', pk=facture.pk)
    else:
        form = LigneFactureForm()
    
    context = {
        'form': form,
        'facture': facture,
    }
    return render(request, 'chantiers/ajouter_ligne_facture.html', context)

@login_required
def supprimer_ligne_facture(request, pk):
    """Supprimer une ligne de facture"""
    ligne = get_object_or_404(LigneFacture, pk=pk)
    facture_pk = ligne.facture.pk
    
    if request.method == 'POST':
        ligne.delete()
        
        # Recalculer le total
        facture = Facture.objects.get(pk=facture_pk)
        total = facture.lignes.aggregate(total=models.Sum('montant'))['total'] or 0
        facture.montant_ht = total
        facture.montant_ttc = total * (1 + facture.tva / 100)
        facture.save()
        
        messages.success(request, 'Ligne supprimée')
        return redirect('detail_facture', pk=facture_pk)
    
    context = {'ligne': ligne}
    return render(request, 'chantiers/supprimer_ligne_facture.html', context)

@login_required
def changer_statut_facture(request, pk, statut):
    """Changer le statut d'une facture"""
    facture = get_object_or_404(Facture, pk=pk)
    facture.statut = statut
    
    if statut == 'PAYEE':
        facture.date_paiement = date.today()
        
        # Créer une transaction dans la caisse
        caisse = Caisse.objects.first()
        if caisse:
            Transaction.objects.create(
                caisse=caisse,
                type_transaction='RECETTE',
                categorie='CLIENT',
                montant=facture.montant_ttc,
                description=f"Paiement facture {facture.numero_facture} - {facture.chantier.nom}",
                chantier=facture.chantier
            )
            caisse.solde_actuel += facture.montant_ttc
            caisse.save()
    
    facture.save()
    messages.success(request, f'Statut de la facture mis à jour : {facture.get_statut_display()}')
    return redirect('detail_facture', pk=facture.pk)

@login_required
def generer_pdf_facture(request, pk):
    """Générer un PDF de facture professionnel"""
    facture = get_object_or_404(Facture, pk=pk)
    
    # Créer le buffer PDF
    buffer = io.BytesIO()
    
    # Créer le canvas
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, facture.societe_nom)
    
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, facture.societe_adresse)
    p.drawString(50, height - 85, f"Tél: {facture.societe_telephone} - Email: {facture.societe_email}")
    p.drawString(50, height - 100, f"SIRET: {facture.societe_siret}")
    
    # Titre FACTURE
    p.setFont("Helvetica-Bold", 20)
    p.drawString(width - 200, height - 80, "FACTURE")
    
    # Numéro de facture
    p.setFont("Helvetica-Bold", 12)
    p.drawString(width - 200, height - 110, f"N° {facture.numero_facture}")
    
    # Date
    p.setFont("Helvetica", 10)
    p.drawString(width - 200, height - 130, f"Date: {facture.date_emission.strftime('%d/%m/%Y')}")
    p.drawString(width - 200, height - 145, f"Échéance: {facture.date_echeance.strftime('%d/%m/%Y')}")
    
    # Trait de séparation
    p.line(50, height - 160, width - 50, height - 160)
    
    # Informations client
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 190, "Client:")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 210, facture.client_nom)
    p.drawString(50, height - 225, facture.client_adresse)
    p.drawString(50, height - 240, f"Tél: {facture.client_telephone}")
    p.drawString(50, height - 255, f"Email: {facture.client_email}")
    
    # Informations chantier
    p.setFont("Helvetica-Bold", 12)
    p.drawString(width - 250, height - 190, "Chantier:")
    p.setFont("Helvetica", 10)
    p.drawString(width - 250, height - 210, facture.chantier.nom)
    p.drawString(width - 250, height - 225, facture.chantier.lieu)
    
    # Trait de séparation
    p.line(50, height - 280, width - 50, height - 280)
    
    # Tableau des lignes
    data = [["Description", "Quantité", "Prix unitaire", "Montant"]]
    
    for ligne in facture.lignes.all():
        data.append([
            ligne.description,
            f"{ligne.quantite}",
            f"{ligne.prix_unitaire:.2f} €",
            f"{ligne.montant:.2f} €"
        ])
    
    # Ligne de total
    data.append(["", "", "TOTAL HT", f"{facture.montant_ht:.2f} €"])
    data.append(["", "", f"TVA ({facture.tva}%)", f"{facture.montant_ttc - facture.montant_ht:.2f} €"])
    data.append(["", "", "TOTAL TTC", f"{facture.montant_ttc:.2f} €"])
    
    # Créer le tableau
    table = Table(data, colWidths=[250, 70, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
        ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    # Positionner le tableau
    table.wrapOn(p, width, height)
    table.drawOn(p, 50, height - 500)
    
    # Conditions
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, height - 550, "Conditions de paiement:")
    p.setFont("Helvetica", 9)
    p.drawString(50, height - 565, facture.conditions)
    
    # Notes
    if facture.notes:
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, height - 590, "Notes:")
        p.setFont("Helvetica", 9)
        p.drawString(50, height - 605, facture.notes)
    
    # Pied de page
    p.setFont("Helvetica", 8)
    p.drawString(50, 50, f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    p.drawString(width - 200, 50, f"Facture {facture.numero_facture}")
    
    # Sauvegarder le PDF
    p.showPage()
    p.save()
    
    # Retourner le PDF
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"facture_{facture.numero_facture}.pdf")    