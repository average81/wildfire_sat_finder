// Базовые функции для работы с API
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
			'Accept': 'application/json',
        },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error('HTTP error! status: ${response.status}');
    }
    return await response.json();
}

// Функции для работы с email адресами
async function getEmails() {
    return await apiRequest('/emails');
}

async function addEmail(email) {
    return await apiRequest('/emails/add', 'POST', { email });
}

async function deleteEmail(id) {
    return await apiRequest('/emails/' + id, 'DELETE');
}

// Функции для работы с регионами
async function getRegions() {
    return await apiRequest('/regions');
}

async function addRegion(region) {
    return await apiRequest('/regions/add', 'POST', region);
}

async function deleteRegion(id) {
    return await apiRequest('/regions/${id}', 'DELETE');
}

// Функции для работы с настройками
async function updateSatService(settings) {
    return await apiRequest('/sat_service', 'PUT', settings);
}

async function updateDetector(settings) {
    return await apiRequest('/detector', 'PUT', settings);
}

// Функции для работы с изображениями
async function uploadTestImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/tstimage', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error('HTTP error! status: ${response.status}');
    }
    return await response.json();
}

async function getTestDetection() {
    return await apiRequest('/tstdetect');
}

async function getAreaImage(params) {
    const queryString = new URLSearchParams(params).toString();
    return await apiRequest('/areaimg?${queryString}');
}

async function getAreaMap(regionId) {
    return await apiRequest('/areamap/${regionId}');
} 