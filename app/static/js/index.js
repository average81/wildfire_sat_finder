document.addEventListener('DOMContentLoaded', function() {
    const satServiceForm = document.getElementById('satServiceForm');
    const detectorForm = document.getElementById('detectorForm');

    satServiceForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(satServiceForm);
        const settings = {
            api_key: formData.get('api_key'),
            base_url: formData.get('base_url'),
            timeout: parseInt(formData.get('timeout'))
        };

        try {
            await updateSatService(settings);
            alert('Настройки сервиса успешно обновлены');
        } catch (error) {
            alert('Ошибка при обновлении настроек: ' + error.message);
        }
    });

    detectorForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(detectorForm);
        const settings = {
            score_threshold: parseFloat(formData.get('score_threshold')),
            min_area: parseFloat(formData.get('min_area'))
        };

        try {
            await updateDetector(settings);
            alert('Настройки детектора успешно обновлены');
        } catch (error) {
            alert('Ошибка при обновлении настроек: ' + error.message);
        }
    });
}); 