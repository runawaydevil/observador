document.addEventListener('DOMContentLoaded', function() {
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
