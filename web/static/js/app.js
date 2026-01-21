document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const mainNav = document.getElementById('main-nav');
    const body = document.body;
    
    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', function() {
            const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true';
            menuToggle.setAttribute('aria-expanded', !isExpanded);
            
            if (!isExpanded) {
                body.classList.add('nav-open');
                mainNav.classList.add('nav-open');
            } else {
                body.classList.remove('nav-open');
                mainNav.classList.remove('nav-open');
            }
        });
        
        mainNav.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                menuToggle.setAttribute('aria-expanded', 'false');
                body.classList.remove('nav-open');
                mainNav.classList.remove('nav-open');
            }
        });
        
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                if (!mainNav.contains(e.target) && !menuToggle.contains(e.target)) {
                    if (menuToggle.getAttribute('aria-expanded') === 'true') {
                        menuToggle.setAttribute('aria-expanded', 'false');
                        body.classList.remove('nav-open');
                        mainNav.classList.remove('nav-open');
                    }
                }
            }
        });
        
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                menuToggle.setAttribute('aria-expanded', 'false');
                body.classList.remove('nav-open');
                mainNav.classList.remove('nav-open');
            }
        });
    }
    
    const consultForm = document.getElementById('consult-form');
    if (consultForm) {
        consultForm.addEventListener('submit', function(e) {
            const loading = document.getElementById('loading');
            if (loading) {
                loading.style.display = 'block';
            }
            
            const question = document.getElementById('question');
            if (question && !question.value.trim()) {
                e.preventDefault();
                if (loading) loading.style.display = 'none';
                return false;
            }
        });
    }
    
    const questionInput = document.getElementById('question');
    if (questionInput) {
        questionInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                if (consultForm) {
                    consultForm.submit();
                }
            }
        });
    }
});
