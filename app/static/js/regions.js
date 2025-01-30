document.addEventListener('DOMContentLoaded', function() {
    const regionForm = document.getElementById('regionForm');
    const regionList = document.getElementById('regionList');

    async function loadRegions() {
        try {
            const regions = await getRegions();
            regionList.innerHTML = '';
            
            for (let i = 0; i < regions.length; i++) {
                const region = regions[i];
                const div = document.createElement('div');
                div.className = 'region-item mb-3 card';
                div.innerHTML = `
                    <div class="card-body">
                        <h6 class="card-title">${region.name}</h6>
                        <p class="card-text">
                            Координаты: (${region.lat1}, ${region.lon1}) - (${region.lat2}, ${region.lon2})
                        </p>
                        <button class="btn btn-danger btn-sm" onclick="deleteRegionHandler(${i})">Удалить</button>
                        <a href="/areamap/${i}" class="btn btn-primary btn-sm">Показать карту</a>
                    </div>
                `;
                regionList.appendChild(div);
            }
        } catch (error) {
            alert('Ошибка при загрузке списка регионов: ' + error.message);
        }
    }

    window.deleteRegionHandler = async function(id) {
        if (typeof id !== 'number') {
            console.error('Invalid id:', id);
            return;
        }
        try {
            await deleteRegion(id);
            await loadRegions();
        } catch (error) {
            alert('Ошибка при удалении региона: ' + error.message);
        }
    };

    regionForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(regionForm);
        const region = {
            name: formData.get('name'),
            lat1: parseFloat(formData.get('lat1')),
            lon1: parseFloat(formData.get('lon1')),
            lat2: parseFloat(formData.get('lat2')),
            lon2: parseFloat(formData.get('lon2'))
        };

        try {
            await addRegion(region);
            regionForm.reset();
            await loadRegions();
        } catch (error) {
            alert('Ошибка при добавлении региона: ' + error.message);
        }
    });

    loadRegions();
}); 