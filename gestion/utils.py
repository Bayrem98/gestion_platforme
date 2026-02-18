from .models import Notification
from django.utils import timezone
from django.urls import reverse

def creer_notification(titre, message, type_notification='INFO', categorie='SYSTEME', lien=None, objet=None):
    """
    Crée une notification
    """
    notification = Notification(
        titre=titre,
        message=message,
        type_notification=type_notification,
        categorie=categorie,
        lien=lien
    )
    
    # Lier à un objet si fourni
    if objet:
        if hasattr(objet, 'employe'):
            notification.employe = objet.employe
        if hasattr(objet, 'transaction'):
            notification.transaction = objet.transaction
        if hasattr(objet, 'chantier'):
            notification.chantier = objet.chantier
    
    notification.save()
    return notification

def notifier_nouvel_employe(employe):
    """Notification quand un nouvel employé est ajouté"""
    titre = f"Nouvel employé : {employe.nom} {employe.prenom}"
    message = f"{employe.nom} {employe.prenom} a été ajouté à l'équipe. Matricule: {employe.matricule}"
    lien = reverse('detail_employe', args=[employe.pk])
    return creer_notification(
        titre=titre,
        message=message,
        type_notification='SUCCESS',
        categorie='EMPLOYE',
        lien=lien,
        objet=employe
    )

def notifier_nouvelle_transaction(transaction):
    """Notification quand une transaction est créée"""
    type_emoji = "💰" if transaction.type_transaction == 'RECETTE' else "💸"
    titre = f"{type_emoji} Nouvelle transaction : {transaction.montant}€"
    message = f"{transaction.description} - {transaction.get_type_transaction_display()}"
    lien = reverse('liste_transactions')
    return creer_notification(
        titre=titre,
        message=message,
        type_notification='SUCCESS' if transaction.type_transaction == 'RECETTE' else 'WARNING',
        categorie='TRANSACTION',
        lien=lien,
        objet=transaction
    )

def notifier_nouveau_planning(planning):
    """Notification quand un planning est ajouté"""
    titre = f"📅 Nouveau planning pour {planning.employe.nom} {planning.employe.prenom}"
    message = f"{planning.date.strftime('%d/%m/%Y')} : {planning.heure_debut}-{planning.heure_fin}"
    lien = reverse('planning_simple', args=[planning.employe.pk])
    return creer_notification(
        titre=titre,
        message=message,
        type_notification='INFO',
        categorie='PLANNING',
        lien=lien,
        objet=planning
    )

def notifier_avance_salaire(avance):
    """Notification pour une avance sur salaire"""
    titre = f"💰 Avance sur salaire : {avance.employe.nom} {avance.employe.prenom}"
    message = f"Montant: {avance.montant}TND - {avance.motif}"
    lien = reverse('detail_employe', args=[avance.employe.pk])
    return creer_notification(
        titre=titre,
        message=message,
        type_notification='WARNING',
        categorie='EMPLOYE',
        lien=lien,
        objet=avance
    )

def notifier_nouveau_chantier(chantier):
    """Notification pour un nouveau chantier"""
    titre = f"🏗️ Nouveau chantier : {chantier.nom}"
    message = f"{chantier.date_debut.strftime('%d/%m/%Y')} - {chantier.date_fin.strftime('%d/%m/%Y')}"
    lien = reverse('detail_chantier', args=[chantier.pk])
    return creer_notification(
        titre=titre,
        message=message,
        type_notification='SUCCESS',
        categorie='CHANTIER',
        lien=lien,
        objet=chantier
    )

def notifier_prime_calculee(prime):
    """Notification pour une prime calculée"""
    titre = f"🎁 Prime calculée : {prime.employe.nom} {prime.employe.prenom}"
    message = f"Montant: {prime.montant}TND - {prime.description}"
    lien = reverse('liste_primes')
    return creer_notification(
        titre=titre,
        message=message,
        type_notification='INFO',
        categorie='PRIME',
        lien=lien,
        objet=prime
    )