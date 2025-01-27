document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const detectionResult = document.getElementById('detectionResult');

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        const file = formData.get('file');

        try {
            await uploadTestImage(file);
            const result = await getTestDetection();
            
            // Отображение результата
            detectionResult.innerHTML = `
                <div class="alert alert-success">
                    <h6>Результат детекции:</h6>
                    <pre>${JSON.stringify(result, null, 2)}</pre>
                </div>
            `;
        } catch (error) {
            detectionResult.innerHTML = `
                <div class="alert alert-danger">
                    Ошибка: ${error.message}
                </div>
            `;
        }
    });
}); 