document.addEventListener('DOMContentLoaded', function() {
    const serviceSelect = document.getElementById('serviceSelect');
    const satServiceForm = document.getElementById('satServiceForm');
    const detectorForm = document.getElementById('detectorForm');

    // Загрузка списка доступных сервисов
    async function loadServices() {
        try {
            const response = await fetch('/sat_services', {
                headers: {
                    'Accept': 'application/json'
                }
            });
            const services = await response.json();
            
            // Получаем активный сервис
            const activeResponse = await fetch('/sat_services/active', {
                headers: {
                    'Accept': 'application/json'
                }
            });
            const activeService = await activeResponse.json();
            
            // Очищаем текущие опции
            serviceSelect.innerHTML = '';
            
            // Добавляем опции для каждого сервиса
            services.forEach((service, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = service;
                // Устанавливаем активный сервис
                if (index === activeService.id) {
                    option.selected = true;
                }
                serviceSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Ошибка при загрузке списка сервисов:', error);
        }
    }

    // Обработчик изменения выбранного сервиса
    serviceSelect.addEventListener('change', async function() {
        const serviceId = parseInt(this.value);  // Преобразуем в число
        try {
            const response = await fetch('/sat_services/active', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ service_id: serviceId })
            });

            if (response.ok) {
                alert('Сервис успешно изменен');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка при изменении сервиса');
            }
        } catch (error) {
            alert('Ошибка при изменении сервиса: ' + error.message);
        }
    });

    // Остальные обработчики форм
    satServiceForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(satServiceForm);
        const settings = {
            api_key: formData.get('api_key'),
            base_url: formData.get('base_url'),
            user_id: formData.get('user_id')
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

    // Загружаем список сервисов при загрузке страницы
    loadServices();
}); 