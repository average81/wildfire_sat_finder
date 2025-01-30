import httpx
import json
import sys

BASE_URL = "http://localhost:8000"

def print_response(endpoint, response):
    print(f"\n=== Testing {endpoint} ===")
    print(f"Status: {response.status_code}")
    try:
        print("Response:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print("Response:", response.text[:200], "..." if len(response.text) > 200 else "")

async def test_endpoints():
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Функция для обновления статистики
            def update_stats(endpoint, response):
                results["total"] += 1
                if response.status_code < 400:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{endpoint}: {response.status_code}")

            # Тест sat_service endpoints
            print("\n=== Testing sat_service endpoints ===")
            
            # GET JSON
            response = await client.get(
                f"{BASE_URL}/sat_service",
                headers={"Accept": "application/json"}
            )
            print_response("/sat_service (JSON)", response)
            update_stats("/sat_service (JSON)", response)

            # GET HTML
            response = await client.get(
                f"{BASE_URL}/sat_service",
                headers={"Accept": "text/html"}
            )
            print_response("/sat_service (HTML)", response)
            update_stats("/sat_service (HTML)", response)

            # PUT settings
            test_settings = {
                "api_key": "test_key",
                "base_url": "test_url",
                "user_id": "test_user"
            }
            response = await client.put(
                f"{BASE_URL}/sat_service",
                json=test_settings
            )
            print_response("/sat_service (PUT)", response)
            update_stats("/sat_service (PUT)", response)

            # Тест detector endpoint
            print("\n=== Testing detector endpoint ===")
            
            # GET JSON
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
            update_stats("/detector (JSON)", response)

            # GET HTML
            response = await client.get(
                f"{BASE_URL}/detector",
                params=params,
                headers={"Accept": "text/html"}
            )
            print_response("/detector (HTML)", response)
            update_stats("/detector (HTML)", response)

            # Тест areaimg с новыми параметрами
            print("\n=== Testing areaimg endpoint ===")
            
            img_params = {
                "lat": 55.0,
                "lon": 37.0,
                "width": 1.0,
                "height": 1.0
            }
            
            # JSON формат
            response = await client.get(
                f"{BASE_URL}/areaimg",
                params=img_params,
                headers={"Accept": "application/json"}
            )
            print_response("/areaimg (JSON)", response)
            update_stats("/areaimg (JSON)", response)

            # HTML формат
            response = await client.get(
                f"{BASE_URL}/areaimg",
                params=img_params,
                headers={"Accept": "text/html"}
            )
            print_response("/areaimg (HTML)", response)
            update_stats("/areaimg (HTML)", response)

    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        sys.exit(1)
    
    # Вывод итоговых результатов
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"Всего тестов: {results['total']}")
    print(f"Успешно: {results['passed']}")
    print(f"Неудачно: {results['failed']}")
    if results["errors"]:
        print("\nОшибки:")
        for error in results["errors"]:
            print(f"- {error}")
    print("="*50)

    # Возвращаем код завершения
    return 0 if results["failed"] == 0 else 1

if __name__ == "__main__":
    print("Начинаем тестирование API endpoints...")
    print(f"Сервер: {BASE_URL}")
    print("Убедитесь, что сервер запущен командой: uvicorn app.main:app --reload")
    print("Порядок запуска:")
    print("1. В первом терминале: uvicorn app.main:app --reload")
    print("2. В другом терминале: python -m app.test_endpoints")
    print("-" * 50)
    
    import asyncio
    sys.exit(asyncio.run(test_endpoints())) 