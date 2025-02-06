document.addEventListener('DOMContentLoaded', function() {
    function updateFiresTable() {
        fetch('/detections', {
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('firesTableBody');
            tbody.innerHTML = '';
            
            data.forEach(fire => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${fire.id}</td>
                    <td>${fire.time}</td>
                    <td>${fire.lat.toFixed(6)}</td>
                    <td>${fire.lon.toFixed(6)}</td>
                    <td>${fire.score.toFixed(2)}</td>
                    <td>${fire.name}</td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error('������ ��� ���������� ������:', error));
    }

    // ��������� ������ ������ 10 ������
    setInterval(updateFiresTable, 10000);
    
    // ������ ���������� ��� �������� ��������
    updateFiresTable();
}); 