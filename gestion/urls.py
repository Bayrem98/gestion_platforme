from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    
    # Employees
    path('employes/', views.liste_employes, name='liste_employes'),
    path('employes/ajouter/', views.ajouter_employe, name='ajouter_employe'),
    path('employes/<int:pk>/', views.detail_employe, name='detail_employe'),
    path('employes/<int:pk>/modifier/', views.modifier_employe, name='modifier_employe'),
    path('employes/<int:pk>/supprimer/', views.supprimer_employe, name='supprimer_employe'),
    path('employes/<int:pk>/avance/', views.ajouter_avance, name='ajouter_avance'),
    
    # Planning URLs
    path('employes/<int:pk>/planning-simple/', views.planning_simple, name='planning_simple'),
    path('employes/<int:pk>/planning-simple/ajouter/', views.ajouter_planning_simple, name='ajouter_planning_simple'),
    path('planning-simple/<int:pk>/modifier/', views.modifier_planning_simple, name='modifier_planning_simple'),
    path('planning-simple/<int:pk>/supprimer/', views.supprimer_planning_simple, name='supprimer_planning_simple'),
    path('employes/<int:pk>/test-planning/', views.test_planning, name='test_planning'),
    
    # Freelancers
    path('freelancers/', views.liste_freelancers, name='liste_freelancers'),
    path('freelancers/ajouter/', views.ajouter_freelancer, name='ajouter_freelancer'),
    path('freelancers/<int:pk>/', views.detail_freelancer, name='detail_freelancer'),
    path('freelancers/<int:pk>/modifier/', views.modifier_freelancer, name='modifier_freelancer'),
    
    # Chantiers
    path('chantiers/', views.liste_chantiers, name='liste_chantiers'),
    path('chantiers/ajouter/', views.ajouter_chantier, name='ajouter_chantier'),
    path('chantiers/<int:pk>/', views.detail_chantier, name='detail_chantier'),
    path('chantiers/<int:pk>/affecter-employe/', views.affecter_employe, name='affecter_employe'),
    path('chantiers/<int:pk>/affecter-freelancer/', views.affecter_freelancer, name='affecter_freelancer'),
    
    # Primes
    path('primes/', views.liste_primes, name='liste_primes'),
    path('primes/calculer/', views.calculer_primes, name='calculer_primes'),
    path('primes/ajouter/', views.ajouter_prime, name='ajouter_prime'),
    path('primes/<int:pk>/payer/', views.payer_prime, name='payer_prime'),
    
    # Finance
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('finance/transaction/ajouter/', views.ajouter_transaction, name='ajouter_transaction'),
    path('finance/transactions/', views.liste_transactions, name='liste_transactions'),
    path('finance/recu/<int:pk>/generer/', views.generer_recu, name='generer_recu'),
    path('finance/recu/<int:pk>/imprimer/', views.imprimer_recu, name='imprimer_recu'),

    # Notifications
    path('notifications/', views.liste_notifications, name='liste_notifications'),
    path('notifications/api/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:pk>/lire/', views.marquer_notification_lue, name='marquer_notification_lue'),
    path('notifications/tout-lire/', views.marquer_tout_lu, name='marquer_tout_lu'),
]