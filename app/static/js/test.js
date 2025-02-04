document.addEventListener('DOMContentLoaded', function() {
    const fileTestBtn = document.getElementById('fileTestBtn');
    const coordTestBtn = document.getElementById('coordTestBtn');
    const fileUpload = document.getElementById('fileUpload');
    const coordInput = document.getElementById('coordInput');
    const uploadForm = document.getElementById('uploadForm');
    const coordForm = document.getElementById('coordForm');

    // Переключение между режимами
    fileTestBtn.addEventListener('click', function(e) {
        e.preventDefault();
        fileTestBtn.classList.add('btn-primary');
        fileTestBtn.classList.remove('btn-outline-primary');
        coordTestBtn.classList.remove('btn-primary');
        coordTestBtn.classList.add('btn-outline-primary');
        fileUpload.style.display = 'block';
        coordInput.style.display = 'none';
    });

    coordTestBtn.addEventListener('click', function(e) {
        e.preventDefault();
        coordTestBtn.classList.add('btn-primary');
        coordTestBtn.classList.remove('btn-outline-primary');
        fileTestBtn.classList.remove('btn-primary');
        fileTestBtn.classList.add('btn-outline-primary');
        fileUpload.style.display = 'none';
        coordInput.style.display = 'block';
    });

    // Обработка загрузки файла
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = uploadForm.querySelector('input[type="file"]');
            if (!fileInput || !fileInput.files.length) {
                alert('Пожалуйста, выберите файл');
                return;
            }
            
            const formData = new FormData(uploadForm);
            
            try {
                const response = await fetch('/tstimage', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                // После успешной загрузки файла делаем запрос на детекцию
                const detectResponse = await fetch('/tstdetect');
                if (!detectResponse.ok) {
                    throw new Error(`Detection error! status: ${detectResponse.status}`);
                }
                
                // Перенаправляем на страницу с результатами
                window.location.href = detectResponse.url;
                
            } catch (error) {
                const resultDiv = document.getElementById('result');
                if (resultDiv) {
                    resultDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${error.message}</div>`;
                }
            }
        });
    }

    // Обработка формы координат
    if (coordForm) {
        coordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(coordForm);
            const lat = formData.get('lat');
            const lon = formData.get('lon');
            const width = formData.get('width');
            const height = formData.get('height');
            
            window.location.href = `/areaimg?lat=${lat}&lon=${lon}&width=${width}&height=${height}`;
        });
    }
});

// Функция для получения изображения по координатам
function getImage() {
    const lat1 = document.getElementById('lat1').value;
    const lon1 = document.getElementById('lon1').value;
    const width = document.getElementById('width').value;
    const height = document.getElementById('height').value;
    
    window.location.href = `/detector?lat1=${lat1}&lon1=${lon1}&lat2=${parseFloat(lat1) + parseFloat(height)}&lon2=${parseFloat(lon1) + parseFloat(width)}`;
} 