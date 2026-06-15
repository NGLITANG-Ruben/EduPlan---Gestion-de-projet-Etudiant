document.addEventListener('DOMContentLoaded', () => {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(f => {
        setTimeout(() => {
            f.style.opacity = '0';
            f.style.transition = 'opacity 0.3s';
            setTimeout(() => f.remove(), 300);
        }, 4000);
    });
});

document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.getElementById('menu-btn');
    if (sidebar && menuBtn && window.innerWidth < 768) {
        if (!sidebar.contains(e.target) && e.target !== menuBtn && !menuBtn.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    }
});