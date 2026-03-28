// main.js
document.addEventListener('DOMContentLoaded', () => {
    // Client-side interactions
    console.log('PriorityTask Intelligence Initialized');

    // Add subtle hover animations to cards
    const cards = document.querySelectorAll('.task-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.borderColor = 'rgba(99, 102, 241, 0.4)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        });
    });

    // Handle form loading states
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', () => {
            const btn = form.querySelector('.btn-primary');
            if (btn) {
                btn.innerHTML = 'Processing...';
                btn.classList.add('loading');
            }
        });
    });
    // Tab Switching Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            if (targetTab === 'vault') {
                fetchVault();
            }
        });
    });

    async function fetchVault() {
        const grid = document.getElementById('vault-grid');
        try {
            const response = await fetch('/api/vault');
            const data = await response.json();
            
            if (!data.tasks || data.tasks.length === 0) {
                grid.innerHTML = '<div class="empty-state">Vault is empty. No tasks were archived recently.</div>';
                return;
            }
            
            grid.innerHTML = data.tasks.map(task => `
                <div class="task-card task-priority-${task.priority} vault-card">
                    <div class="task-header">
                        <h3>${task.name}</h3>
                        <span class="badge priority-badge">P${task.priority}</span>
                    </div>
                    <div class="task-details">
                        <p><strong>Original Hours:</strong> ${task.hours_per_day} hrs/day</p>
                        <p><strong>Dropped At:</strong> ${new Date(task.dropped_at).toLocaleDateString()}</p>
                    </div>
                    <div class="vault-mark">SECURED</div>
                </div>
            `).join('');
        } catch (error) {
            grid.innerHTML = '<div class="empty-state text-danger">Error loading vault tasks.</div>';
            console.error('Fetch error:', error);
        }
    }
});
