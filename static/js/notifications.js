// Gestionnaire de notifications
class NotificationManager {
    constructor() {
        this.interval = null;
        this.init();
    }

    init() {
        this.loadNotifications();
        // Rafraîchir toutes les 30 secondes
        this.interval = setInterval(() => this.loadNotifications(), 30000);
        this.setupEventListeners();
    }

    async loadNotifications() {
        try {
            const response = await fetch('/notifications/api/');
            const data = await response.json();
            this.updateUI(data);
        } catch (error) {
            console.error('Erreur chargement notifications:', error);
        }
    }

    updateUI(data) {
        // Mettre à jour le compteur
        const countBadge = document.getElementById('notificationCount');
        if (countBadge) {
            countBadge.textContent = data.count;
            if (data.count > 0) {
                countBadge.style.display = 'inline';
            } else {
                countBadge.style.display = 'none';
            }
        }

        // Mettre à jour la liste
        const notifList = document.getElementById('notificationList');
        if (notifList) {
            if (data.notifications.length === 0) {
                notifList.innerHTML = `
                    <div class="text-center p-4 text-muted">
                        <i class="fas fa-bell-slash fa-2x mb-2"></i>
                        <p>Aucune nouvelle notification</p>
                    </div>
                `;
            } else {
                notifList.innerHTML = data.notifications.map(n => this.renderNotification(n)).join('');
            }
        }
    }

    renderNotification(n) {
        const bgClass = n.type === 'SUCCESS' ? 'bg-success' :
                       n.type === 'WARNING' ? 'bg-warning' :
                       n.type === 'DANGER' ? 'bg-danger' : 'bg-info';
        
        return `
            <div class="dropdown-item notification-item" data-id="${n.id}" style="white-space: normal; border-bottom: 1px solid #eee;">
                <div class="d-flex align-items-start">
                    <div class="me-2">
                        <span class="badge ${bgClass} p-2">
                            <i class="${n.icone.icon}"></i>
                        </span>
                    </div>
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between">
                            <strong>${n.titre}</strong>
                            <small class="text-muted">${n.time_ago}</small>
                        </div>
                        <p class="small mb-1">${n.message}</p>
                        ${n.lien ? `<a href="${n.lien}" class="small text-primary">Voir détails →</a>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    async markAsRead(notificationId) {
        try {
            await fetch(`/notifications/${notificationId}/lire/`);
            this.loadNotifications();
        } catch (error) {
            console.error('Erreur:', error);
        }
    }

    async markAllRead() {
        try {
            await fetch('/notifications/tout-lire/');
            this.loadNotifications();
        } catch (error) {
            console.error('Erreur:', error);
        }
    }

    setupEventListeners() {
        // Marquer tout comme lu
        document.getElementById('markAllRead')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.markAllRead();
        });

        // Marquer individuellement au clic
        document.addEventListener('click', (e) => {
            const item = e.target.closest('.notification-item');
            if (item && !e.target.closest('a')) {
                const id = item.dataset.id;
                this.markAsRead(id);
            }
        });

        // Rafraîchir au focus
        window.addEventListener('focus', () => this.loadNotifications());
    }
}

// Initialiser quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    new NotificationManager();
});