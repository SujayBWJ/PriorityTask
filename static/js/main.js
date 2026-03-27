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
});
