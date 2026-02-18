// main.js - Scripts personnalisés
console.log('Application chargée avec succès!');

// Activer les tooltips Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Confirmation avant suppression
function confirmDelete(message) {
    return confirm(message || 'Êtes-vous sûr de vouloir supprimer cet élément ?');
}

// Gestion du menu paramètres
document.addEventListener('DOMContentLoaded', function() {
    
    // Rafraîchir les données
    document.getElementById('refreshData')?.addEventListener('click', function(e) {
        e.preventDefault();
        location.reload();
    });

    // Mode sombre (optionnel)
    const darkModeSwitch = document.getElementById('darkModeSwitch');
    if (darkModeSwitch) {
        // Vérifier si le mode sombre est déjà activé
        if (localStorage.getItem('darkMode') === 'enabled') {
            document.body.classList.add('dark-mode');
            darkModeSwitch.checked = true;
        }

        darkModeSwitch.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('dark-mode');
                localStorage.setItem('darkMode', 'enabled');
            } else {
                document.body.classList.remove('dark-mode');
                localStorage.setItem('darkMode', 'disabled');
            }
        });
    }
});

// Raccourcis clavier
document.addEventListener('keydown', function(e) {
    // Ctrl + N : Nouvel employé
    if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/employes/ajouter/';
    }
    // Ctrl + Shift + P : Planning
    if (e.ctrlKey && e.shiftKey && e.key === 'P') {
        e.preventDefault();
        // Rediriger vers le dernier employé consulté ou page planning
    }
});