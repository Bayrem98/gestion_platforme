// Gestion du champ "Autre poste"
document.addEventListener('DOMContentLoaded', function() {
    const posteChoice = document.getElementById('id_poste_choice');
    const posteAutre = document.getElementById('id_poste_autre');
    const autrePosteContainer = document.getElementById('autre_poste_container');
    
    if (!posteChoice || !posteAutre) {
        console.log('Éléments non trouvés');
        return;
    }
    
    function togglePosteAutre() {
        if (posteChoice.value === 'AUTRE') {
            autrePosteContainer.style.display = 'block';
            posteAutre.required = true;
        } else {
            autrePosteContainer.style.display = 'none';
            posteAutre.required = false;
            posteAutre.value = ''; // Vider si on change d'option
        }
    }
    
    // Initialisation
    togglePosteAutre();
    
    // Écouter les changements
    posteChoice.addEventListener('change', togglePosteAutre);
    
    // Debug : afficher les valeurs des dates
    const dateNaissance = document.getElementById('id_date_naissance');
    const dateEmbauche = document.getElementById('id_date_embauche');
    
    console.log('Date naissance:', dateNaissance ? dateNaissance.value : 'non trouvé');
    console.log('Date embauche:', dateEmbauche ? dateEmbauche.value : 'non trouvé');
});