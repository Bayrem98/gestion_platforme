from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from .models import *

class ChantierAdmin(admin.ModelAdmin):
    list_display = ['nom', 'date_debut', 'date_fin', 'statut', 'progression', 'jours_restants']
    list_filter = ['statut', 'type_chantier']
    actions = ['mettre_a_jour_statuts']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('mettre-a-jour-tous/', self.admin_site.admin_view(self.mettre_a_jour_tous), name='mettre-a-jour-tous'),
        ]
        return custom_urls + urls
    
    def mettre_a_jour_tous(self, request):
        count = 0
        for chantier in Chantier.objects.all():
            ancien = chantier.statut
            nouveau = chantier.mettre_a_jour_statut()
            if ancien != nouveau:
                count += 1
        
        messages.success(request, f'{count} chantier(s) mis à jour')
        return redirect('admin:gestion_chantier_changelist')
    
    mettre_a_jour_tous.short_description = "Mettre à jour tous les statuts"
    
    def mettre_a_jour_statuts(self, request, queryset):
        count = 0
        for chantier in queryset:
            ancien = chantier.statut
            nouveau = chantier.mettre_a_jour_statut()
            if ancien != nouveau:
                count += 1
        self.message_user(request, f'{count} chantier(s) mis à jour')
    mettre_a_jour_statuts.short_description = "Mettre à jour les statuts sélectionnés"

admin.site.register(Chantier, ChantierAdmin)