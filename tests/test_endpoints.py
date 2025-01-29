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
    try:
        async with httpx.AsyncClient() as client:
            # Проверка доступности сервера
            try:
                response = await client.get(f"{BASE_URL}/")
            except httpx.ConnectError:
                print(f"Ошибка: Не удалось подключиться к серверу {BASE_URL}")
                print("Убедитесь, что сервер запущен командой: uvicorn app.main:app --reload")
                sys.exit(1)

            # Тест всех GET эндпоинтов в обоих форматах
            endpoints = [
                "/",
                "/emails",
                "/regions",
                "/tstimage",
                "/areaimg?lat1=55.0&lon1=37.0&lat2=56.0&lon2=38.0&width=800&height=600",
            ]

            print("\n=== Тестирование GET endpoints ===")
            for endpoint in endpoints:
                # JSON формат
                print(f"\nТестирование {endpoint} (JSON)")
                response = await client.get(
                    f"{BASE_URL}{endpoint}", 
                    headers={"Accept": "application/json"}
                )
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

                # HTML формат
                print(f"\nТестирование {endpoint} (HTML)")
                response = await client.get(
                    f"{BASE_URL}{endpoint}", 
                    headers={"Accept": "text/html"}
                )
                print(f"Status: {response.status_code}")
                print(f"Content length: {len(response.text)}")

            # Тест /areamap с существующим регионом
            print("\n=== Тестирование /areamap ===")
            # Сначала создаем регион
            test_region = {
                "name": "Тестовый регион",
                "lat1": 55.0,
                "lon1": 37.0,
                "lat2": 56.0,
                "lon2": 38.0
            }
            response = await client.post(f"{BASE_URL}/regions/add", json=test_region)
            region_id = response.json()["id"]

            # Тестируем /areamap в обоих форматах
            for accept in ["application/json", "text/html"]:
                try:
                    response = await client.get(
                        f"{BASE_URL}/areamap/{region_id}",
                        headers={"Accept": accept}
                    )
                    print(f"\nТестирование /areamap/{region_id} ({accept})")
                    print(f"Status: {response.status_code}")
                    if response.status_code >= 500:
                        print("Error response:", response.text)
                    elif accept == "application/json" and response.status_code == 200:
                        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
                    else:
                        print(f"Content length: {len(response.text)}")
                except Exception as e:
                    print(f"Ошибка при тестировании /areamap/{region_id} ({accept}): {str(e)}")

            # Тест POST и PUT endpoints
            print("\n=== Тестирование POST/PUT endpoints ===")
            
            # Test /emails/add
            test_email = {"email": "test@example.com"}
            response = await client.post(f"{BASE_URL}/emails/add", json=test_email)
            print_response("/emails/add (POST)", response)

            # Test /regions/add
            response = await client.post(f"{BASE_URL}/regions/add", json=test_region)
            print_response("/regions/add (POST)", response)

            # Test /sat_service
            test_settings = {
                "api_key": "test_key",
                "base_url": "http://test.com",
                "timeout": 30
            }
            response = await client.put(f"{BASE_URL}/sat_service", json=test_settings)
            print_response("/sat_service (PUT)", response)

            # Test /detector
            detector_settings = {
                "score_threshold": 0.5,
                "min_area": 100.0
            }
            response = await client.put(f"{BASE_URL}/detector", json=detector_settings)
            print_response("/detector (PUT)", response)

    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Начинаем тестирование API endpoints...")
    print(f"Сервер: {BASE_URL}")
    print("Убедитесь, что сервер запущен командой: uvicorn app.main:app --reload")
    print("Порядок запуска:")
    print("1. В первом терминале: uvicorn app.main:app --reload")
    print("2. В другом терминале: python -m app.test_endpoints")
    print("-" * 50)
    
    import asyncio
    asyncio.run(test_endpoints()) 