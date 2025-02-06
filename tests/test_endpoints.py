import httpx
import json
import sys
from fastapi.testclient import TestClient
from app.main import app

# Устанавливаем кодировку для вывода
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"

def print_response(endpoint, response):
    print(f"\n=== Testing {endpoint} ===")
    print(f"Status: {response.status_code}")
    try:
        print("Response:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        # Ограничиваем вывод HTML и добавляем кодировку
        print("Response:", response.text[:200].encode('utf-8').decode('utf-8'), 
              "..." if len(response.text) > 200 else "")

def update_stats(endpoint, response, results):
    if response.status_code < 400:
        results["passed"] += 1
    else:
        results["failed"] += 1
        print(f"❌ Error testing {endpoint}: {response.status_code}")

async def test_endpoints():
    results = {"passed": 0, "failed": 0}

    try:
        async with httpx.AsyncClient() as client:
            # Тест emails endpoints
            print("\n=== Testing emails endpoints ===")
            
            # GET emails
            response = await client.get(
                f"{BASE_URL}/emails",
                headers={"Accept": "application/json"}
            )
            print_response("/emails", response)
            update_stats("/emails", response, results)

            # POST email
            response = await client.post(
                f"{BASE_URL}/emails/add",
                json={"email": "test@example.com"}
            )
            print_response("/emails/add", response)
            update_stats("/emails/add", response, results)

            # Тест regions endpoints
            print("\n=== Testing regions endpoints ===")
            
            # GET regions
            response = await client.get(
                f"{BASE_URL}/regions",
                headers={"Accept": "application/json"}
            )
            print_response("/regions", response)
            update_stats("/regions", response, results)

            # POST region
            test_region = {
                "name": "Test Region",
                "lat1": 55.0,
                "lon1": 37.0,
                "lat2": 56.0,
                "lon2": 38.0
            }
            response = await client.post(
                f"{BASE_URL}/regions/add",
                json=test_region
            )
            print_response("/regions/add", response)
            update_stats("/regions/add", response, results)

            # Тест sat_service endpoints
            print("\n=== Testing sat_service endpoints ===")
            
            # GET JSON
            response = await client.get(
                f"{BASE_URL}/sat_service",
                headers={"Accept": "application/json"}
            )
            print_response("/sat_service (JSON)", response)
            update_stats("/sat_service (JSON)", response, results)

            # GET HTML
            response = await client.get(
                f"{BASE_URL}/sat_service",
                headers={"Accept": "text/html"}
            )
            print_response("/sat_service (HTML)", response)
            update_stats("/sat_service (HTML)", response, results)

            # PUT settings
            test_settings = {
                "api_key": "test_key",
                "user_id": "test_user"
            }
            response = await client.put(
                f"{BASE_URL}/sat_service",
                json=test_settings
            )
            print_response("/sat_service (PUT)", response)
            update_stats("/sat_service (PUT)", response, results)

            # Тест detector endpoint
            print("\n=== Testing detector endpoint ===")
            params = {
                "lat1": 55.0,
                "lon1": 37.0,
                "lat2": 56.0,
                "lon2": 38.0
            }
            response = await client.get(
                f"{BASE_URL}/detector",
                params=params,
                headers={"Accept": "application/json"}
            )
            print_response("/detector (JSON)", response)
            update_stats("/detector", response, results)

            # Тест sat_services endpoints
            print("\n=== Testing sat_services endpoints ===")
            response = await client.get(
                f"{BASE_URL}/sat_services",
                headers={"Accept": "application/json"}
            )
            print_response("/sat_services", response)
            update_stats("/sat_services", response, results)

            # Тест активного сервиса
            response = await client.get(
                f"{BASE_URL}/sat_services/active",
                headers={"Accept": "application/json"}
            )
            print_response("/sat_services/active", response)
            update_stats("/sat_services/active", response, results)

            # Установка активного сервиса
            response = await client.post(
                f"{BASE_URL}/sat_services/active",
                json={"service_id": 0}
            )
            print_response("/sat_services/active (POST)", response)
            update_stats("/sat_services/active (POST)", response, results)

            # Тест получения списка детекций
            print("\n=== Testing detections endpoints ===")
            
            # GET all detections
            response = await client.get(
                f"{BASE_URL}/detections",
                headers={"Accept": "application/json"}
            )
            print_response("/detections", response)
            update_stats("/detections", response, results)

            # GET detections by period
            params = {
                "start_time": "2024-01-01 00:00:00",
                "end_time": "2024-12-31 23:59:59"
            }
            response = await client.get(
                f"{BASE_URL}/detections/period",
                params=params,
                headers={"Accept": "application/json"}
            )
            print_response("/detections/period", response)
            update_stats("/detections/period", response, results)

    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        sys.exit(1)
    
    # Вывод результатов тестирования
    print(f"\nРезультаты тестирования:")
    print(f"✅ Успешно: {results['passed']}")
    print(f"❌ Ошибок: {results['failed']}")
    
    return 0 if results["failed"] == 0 else 1

if __name__ == "__main__":
    print("Начинаем тестирование API endpoints...")
    print(f"Сервер: {BASE_URL}")
    print("Убедитесь, что сервер запущен командой: uvicorn app.main:app --reload")
    print("Порядок запуска:")
    print("1. В первом терминале: uvicorn app.main:app --reload")
    print("2. В другом терминале: python -m tests.test_endpoints")
    print("-" * 50)
    
    import asyncio
    sys.exit(asyncio.run(test_endpoints())) 