from fastapi import FastAPI, HTTPException, Request, Response, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from searcher.searcher import fire_searcher
from fastapi.staticfiles import StaticFiles
from sat_service.sat_service import sat_img_service, SatServiceSettings
import cv2
import numpy as np
import base64
from detector.detector import obj_detector
from repository.repository import *

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")




# Ф-я нанесения рамок на изображение
def draw_box(img, box, id, color=(0, 255, 0), thickness=2):
    cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), color, thickness)
    # Устанавливаем шрифт, размер и цвет текста
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    color = (255, 0, 0)
    thickness = 2

    # Добавляем текст на изображение
    cv2.putText(img, str(id), (box[0], box[1] - 3), font, font_scale, color, thickness, cv2.LINE_AA)
    return img

# Основной маршрут
@app.get("/")
async def root(request: Request):
    if request.headers.get('Accept') == 'application/json':
        # Возвращаем общую информацию о микросервисе в формате JSON
        return JSONResponse(content={
            "name": "Сервис мониторинга аномалий",
            "version": "1.0",
            "description": "Микросервис для мониторинга и детектирования аномалий на спутниковых снимках",
            "endpoints": {
                "emails": "/emails",
                "regions": "/regions",
                "test": "/tstimage",
                "settings": {
                    "sat_service": "/sat_service",
                    "detector": "/detector"
                }
            }
        })
    # Возвращаем HTML страницу с настройками
    return templates.TemplateResponse("index.html", {"request": request, "active_page": "monitoring"})
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Управление email адресами
# Запрос адресов для уведомлений
@app.get("/emails")
async def get_emails(request: Request):
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content=wildfire_params_repository.get_emails())  # возвращаем список
    return templates.TemplateResponse("emails.html", {"request": request, "active_page": "emails"})

# Добавление нового адреса для уведомления
@app.post("/emails/add")
async def add_email(email: Email):
    id = wildfire_params_repository.add_email(email.email)  # Просто добавляем email в список
    return {"id": id, "email": email.email}  # Возвращаем индекс как id

# Удаление адреса для уведомления
@app.delete("/emails/{email_id}")
async def delete_email(email_id: int):
    try:
        wildfire_params_repository.remove_email(email_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=e)
    return {"message": "Email deleted"}

# Управление регионами
# Запрос регионов наблюдения
@app.get("/regions")
async def get_regions(request: Request):
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content=wildfire_params_repository.get_regions())  # возвращаем список
    return templates.TemplateResponse("regions.html", {"request": request, "active_page": "regions"})

# Создание нового региона наблюдения
@app.post("/regions/add")
async def add_region(region: Region):
    id = wildfire_params_repository.add_region(region.dict())  # добавляем регион в список
    fire_searcher.search_area_update()
    return {"id": id, "region": region.dict()}

# Удаление региона наблюдения
@app.delete("/regions/{region_id}")
async def delete_region(region_id: int):
    try:
        wildfire_params_repository.remove_region(region_id)
        fire_searcher.search_area_update()
    except Exception as e:
        raise HTTPException(status_code=404, detail=e)
    return {"message": "Region deleted"}

# Работа с изображениями
# Запрос изображения с нанесенными рамками найденных объектов и метриками
@app.get("/areaimg")
async def get_area_image(
    request: Request,
    lat: float,
    lon: float,
    width: float,
    height: float
):
    objects = []
    try:
        # Получаем изображение через сервис
        img = sat_img_service.get_image(lat, lon, width, height)
        if img:
            # Конвертируем изображение из PIL в формат для отображения
            img2 = np.array(img.convert("RGB"))
            img = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
            max = np.max(img)
            if max > 0:
                img = img * (255.0 / max)
                img = img.astype(np.uint8)
                #img2 = img2 * (255.0 / max)
                #img2 = img2.astype(np.uint8)
            #Детектируем аномалии
            prediction = obj_detector.detect(img2)
            if len(prediction) > 0:

                for pred in prediction:
                    draw_box(img, pred['box'], pred['type_id'], (0, 255, 0), 2)

                    # Создаем список объектов на изображении с доступной информацией
                    objects.append({
                        'id': pred['type_id'],  # Используем type_id из результатов детектора
                        'type_id': pred['type_id'],  # ID типа
                        'type': pred['type_name'],  # Название типа объекта
                        'score': pred['score'],  # Вероятность
                        'box': pred['box']  # Координаты рамки
                    })

            ret, buffer = cv2.imencode('.jpg', img)
            encoded_img = base64.b64encode(buffer.tobytes()).decode('utf-8')
        else:
            encoded_img = None
    except Exception as e:
        print(f"Error getting image: {str(e)}")
        encoded_img = None


    # Если запрос JSON, возвращаем ответ в формате JSON
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "coordinates": {
                "lat1": lat, "lon1": lon,
                "width": width, "height": height
            },
            "objects": objects,
            "encoded_img": encoded_img
        })


    # Если запрос html, возвращаем страницу
    return templates.TemplateResponse("image.html", {
        "request": request,
        "coordinates": {
            "lat1": lat,
            "lon1": lon,
            "width": width,
            "height": height,
            "objects": objects  # Передаем полный список объектов
        },
        "encoded_img": encoded_img,
        "active_page": "test"
    })

# Запрос сохраненного изображения для теста
@app.get("/tstimage")
async def test_page(request: Request):
    try:
        img = cv2.imread("testimage.jpg")
    except Exception as e:
        img = None
    if img is None:
        return {"message": "Test image not found"}
    ret, buffer = cv2.imencode('.jpg', img)
    encoded_img = base64.b64encode(buffer.tobytes()).decode('utf-8')
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "encoded_img": encoded_img
        })
    return templates.TemplateResponse("test.html", {"request": request, "encoded_img": encoded_img, "active_page": "test"})

# Загрузка изображения для теста
@app.post("/tstimage")
async def upload_test_image(file: UploadFile = File(...)):
    #Преобразуем изображение в jpg
    img = cv2.imdecode(np.frombuffer(file.file.read(), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return {"message": "Test image not found"}
    #Сохраняем тестовое изображение в файл
    cv2.imwrite("testimage.jpg", img)
    return {"filename": file.filename}

# Запрос результата работы детектора на тестовом изображении
@app.get("/tstdetect")
async def test_detect(request: Request):
    # Открываем тестовое изображение, если оно есть
    img = cv2.imread("testimage.jpg")
    if img is None:
        return {"message": "Test image not found"}
    img2 = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    # Запускаем детектор
    objects = []
    prediction = obj_detector.detect(img2)
    for pred in prediction:
        draw_box(img, pred['box'], pred['type_id'], (0, 255, 0), 2)
        # Создаем список объектов на изображении с доступной информацией
        objects.append({
            'id': pred['type_id'],
            'type_id': pred['type_id'],
            'type': pred['type_name'],
            'score': pred['score'],
            'box': pred['box']
        })

    ret, buffer = cv2.imencode('.jpg', img)
    encoded_img = base64.b64encode(buffer.tobytes()).decode('utf-8')

    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "objects": objects,
            "encoded_img": encoded_img
        })

    return templates.TemplateResponse("image.html", {
        "request": request,
        "coordinates": {
            "lat1": 0,
            "lon1": 0,
            "width": 0,
            "height": 0,
            "objects": objects  # Передаем полный список объектов
        },
        "encoded_img": encoded_img,
        "active_page": "test"
    })

# Запрос карты заданного региона с метками пожаров (пока не реализовано)
@app.get("/areamap/{region_id}")
async def get_area_map(request: Request, region_id: int):
    regions = wildfire_params_repository.get_regions()
    if region_id > len(regions):
        raise HTTPException(status_code=404, detail="Region not found")
    region = regions[region_id - 1]
    
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "region_id": region_id,
            "region_data": region,
            "message": "Area map retrieval not implemented yet"
        })
    return templates.TemplateResponse("map.html", {
        "request": request, 
        "active_page": "regions",
        "region": region
    })

# Запрос параметров спутникового сервиса
@app.get("/sat_service")
async def get_sat_service(request: Request):
    params = sat_img_service.get_params()
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "current_settings": {
                "api_key": params.api_key,
                "user_id": params.user_id,
            }
        })
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_settings": {
            "api_key": params.api_key,
            "user_id": params.user_id,
        },
        "active_page": "settings"
    })

# Запись параметров спутникового сервиса
@app.put("/sat_service")
async def configure_sat_service(settings: SatServiceSettings):
    sat_img_service.set_params(settings)
    return JSONResponse(content={
            "current_settings": {
                "api_key": settings.api_key,
                "user_id": settings.user_id,
            }
        })


#Обработка запроса параметров детектора
@app.get("/detector")
async def get_detector(
    request: Request,
):
    min_area = obj_detector.model.min_area
    score_threshold = obj_detector.model.confidence
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "score_threshold": score_threshold,
            "min_area": min_area
        })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "settings",
        "score_threshold": score_threshold,
        "min_area": min_area,
        "message": ""
    })

# Запись параметров детектора
@app.put("/detector")
async def put_detector(
        request: Request,
):
    #Получаем параметры из тела сообщения
    body = await request.json()
    score_threshold = body.get('score_threshold')
    min_area = body.get('min_area')
    obj_detector.model.confidence = score_threshold
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "score_threshold": score_threshold,
            "min_area": min_area
        })

    result = {
        "status": "success",
        "message": f"Score threshold set to {score_threshold}, min area set to {min_area}"
    }
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "settings",
        "score_threshold": score_threshold,
        "min_area": min_area,
        "message": result["message"]
    })

# Запрос имен спутниковых сервисов
@app.get("/sat_services")
async def get_available_services(request: Request):
    services = sat_img_service.get_services()
    service_names = [type(s).__name__ for s in services]
    
    if (request.headers.get('Accept') == 'application/json' or 
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
        return JSONResponse(content=service_names)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "settings",
        "services": service_names
    })

# Установка активного сервиса
@app.post("/sat_services/active")
async def set_active_service(request: Request):
    try:
        body = await request.json()
        service_id = int(body.get('service_id'))
        sat_img_service.Set_active_service(service_id)
        result = {
            "status": "success",
            "message": f"Active service set to {service_id}"
        }
        
        if request.headers.get('Accept') == 'application/json':
            return JSONResponse(content=result)
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "active_page": "settings",
            "message": result["message"]
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Запрос активного сервиса
@app.get("/sat_services/active")
async def get_active_service(request: Request):
    active = sat_img_service.active_service
    active_info = {
        "active_service": type(active).__name__,
        "id": sat_img_service.services.index(active)
    }
    
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content=active_info)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "settings",
        "active_service": active_info
    })

# Запрос таблицы обнаружений объектов
@app.get("/detections/period")
async def get_detections(request: Request, start_time: str, end_time: str):
    # Преобразуем время из строки в datetime
    start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    detections = wildfire_params_repository.get_detections(start_time, end_time)
    #Создаем список для json
    detections_list = []
    for detection in detections:
        detections_list.append({
            "id": detection.id,
            "time": str(detection.time),
            "lat": (detection.lat1 + detection.lat2) / 2,
            "lon": (detection.lon1 + detection.lon2) / 2,
            "score": detection.score,
            "name": detection.name
        })
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content=detections_list)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "detections",
        "detections": detections_list
    })

# Запрос всей таблицы обнаружений объектов
@app.get("/detections")
async def get_detections(request: Request):
    detections = wildfire_params_repository.get_all_detections()
    #Создаем список для json
    detections_list = []
    for detection in detections:
        detections_list.append({
            "id": detection.id,
            "time": str(detection.time),
            "lat": (detection.lat1 + detection.lat2) / 2,
            "lon": (detection.lon1 + detection.lon2) / 2,
            "score": detection.score,
            "name": detection.name
        })
        print(detection.time)
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content=detections_list)

    return templates.TemplateResponse("fires.html", {
        "request": request,
        "detections_list": detections_list,
        "active_page": "fires"
    })