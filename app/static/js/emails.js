document.addEventListener('DOMContentLoaded', function() {
    const emailForm = document.getElementById('emailForm');
    const emailList = document.getElementById('emailList');

    async function loadEmails() {
        try {
            const emails = await getEmails();
            emailList.innerHTML = '';
            
            for (let i = 0; i < emails.length; i++) {
                const div = document.createElement('div');
                div.className = 'email-item d-flex justify-content-between align-items-center mb-2';
                div.innerHTML = `
                    <span>${emails[i]}</span>
                    <button class="btn btn-danger btn-sm" onclick="deleteEmailHandler(${i})">Удалить</button>
                `;
                emailList.appendChild(div);
            }
        } catch (error) {
            alert('Ошибка при загрузке списка email: ' + error.message);
        }
    }

    window.deleteEmailHandler = async function(id) {
        if (typeof id !== 'number') {
            console.error('Invalid id:', id);
            return;
        }
        try {
            await deleteEmail(id);
            await loadEmails();
        } catch (error) {
            alert('Ошибка при удалении email: ' + error.message);
        }
    };

    emailForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(emailForm);
        const email = formData.get('email');

        try {
            await addEmail(email);
            emailForm.reset();
            await loadEmails();
        } catch (error) {
            alert('Ошибка при добавлении email: ' + error.message);
        }
    });

    loadEmails();
}); 