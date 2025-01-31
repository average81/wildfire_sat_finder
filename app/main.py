import httpx
from fastapi import FastAPI, HTTPException, Request, Response, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from sat_service.sat_service import sat_img_service
import cv2
import numpy as np
import base64
from detector.detector import obj_detector

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Модели данных
class Email(BaseModel):
    email: str

class Region(BaseModel):
    name: str
    lat1: float
    lon1: float
    lat2: float
    lon2: float

class SatServiceSettings(BaseModel):
    api_key: str
    base_url: str
    user_id: str

class DetectorSettings(BaseModel):
    score_threshold: float
    min_area: float

# Временное хранилище данных (в реальном приложении использовать базу данных)
emails = []  # список объектов
regions = []  # список объектов

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

# Управление email адресами
@app.get("/emails")
async def get_emails(request: Request):
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content=emails)  # возвращаем список
    return templates.TemplateResponse("emails.html", {"request": request, "active_page": "emails"})

@app.post("/emails/add")
async def add_email(email: Email):
    emails.append(email.email)  # Просто добавляем email в список
    return {"id": len(emails) - 1, "email": email.email}  # Возвращаем индекс как id

@app.delete("/emails/{email_id}")
async def delete_email(email_id: int):
    if email_id >= len(emails):
        raise HTTPException(status_code=404, detail="Email not found")
    del emails[email_id]
    return {"message": "Email deleted"}

# Управление регионами
@app.get("/regions")
async def get_regions(request: Request):
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content=regions)
    return templates.TemplateResponse("regions.html", {"request": request, "active_page": "regions"})

@app.post("/regions/add")
async def add_region(region: Region):
    regions.append(region.dict())  # добавляем регион в список
    return {"id": len(regions) - 1, "region": region.dict()}

@app.delete("/regions/{region_id}")
async def delete_region(region_id: int):
    if region_id >= len(regions):
        raise HTTPException(status_code=404, detail="Region not found")
    del regions[region_id]
    return {"message": "Region deleted"}

# Работа с изображениями
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
            #print(np.max(img))
            if np.max(img) > 0:
                img = img * (255.0 / np.max(img))
                img = img.astype(np.uint8)
                img2 = img2 * (255.0 / np.max(img))
                img2 = img2.astype(np.uint8)
            #Детектируем аномалии

            prediction = obj_detector.detect(img2)
            if len(prediction) > 0:
                for pred in prediction:
                    cv2.rectangle(img, (pred['box'][0], pred['box'][1]), (pred['box'][2], pred['box'][3]), (0, 255, 0), 2)
                    # Устанавливаем шрифт, размер и цвет текста
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 1
                    color = (255, 0, 0)
                    thickness = 2

                    # Добавляем текст на изображение
                    cv2.putText(img, str(pred['type_id']), (pred['box'][0], pred['box'][1] - 3), font, font_scale, color, thickness, cv2.LINE_AA)
                    #Создаем список объектов на изображении
                    objects.append(pred)
            ret, buffer = cv2.imencode('.jpg', img)
            encoded_img = base64.b64encode(buffer.tobytes()).decode('utf-8')
        else:
            encoded_img = None
    except Exception as e:
        print(f"Error getting image: {str(e)}")
        encoded_img = None



    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "coordinates": {
                "lat1": lat, "lon1": lon,
                "width": width, "height": height
            },
            "message": "Image retrieval not implemented yet"
        })



    return templates.TemplateResponse("image.html", {
        "request": request,
        "coordinates": {
            "lat1": lat,
            "lon1": lon,
            "width": width,
            "height": height,
            "objects": objects
        },
        "encoded_img": encoded_img,
        "active_page": "test"
    })

@app.get("/tstimage")
async def test_page(request: Request):
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "description": "Endpoint для тестирования детектора аномалий",
            "methods": {
                "GET": "Получить страницу тестирования",
                "POST": "Загрузить тестовое изображение"
            }
        })
    return templates.TemplateResponse("test.html", {"request": request, "active_page": "test"})

@app.post("/tstimage")
async def upload_test_image(file: UploadFile = File(...)):
    # Здесь будет логика сохранения тестового изображения
    return {"filename": file.filename}

@app.get("/tstdetect")
async def test_detect():
    # Здесь будет логика работы детектора
    return {"message": "Detection not implemented yet"}

@app.get("/areamap/{region_id}")
async def get_area_map(request: Request, region_id: int):
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

# Настройка модулей
@app.get("/sat_service")
async def get_sat_service(request: Request):
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "current_settings": {
                "api_key": "current_key",
                "base_url": "current_url",
                "user_id": "current_user"
            },
            "available_services": [
                {
                    "name": "Sentinel-2",
                    "description": "Европейский спутник с разрешением 10м",
                    "base_url": "sentinel_url"
                },
                {
                    "name": "Landsat-8",
                    "description": "Американский спутник с разрешением 30м",
                    "base_url": "landsat_url"
                }
            ]
        })
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "active_page": "settings"
    })

@app.put("/sat_service")
async def configure_sat_service(settings: SatServiceSettings):
    # Здесь будет логика настройки сервиса спутниковых снимков
    return settings

@app.get("/detector")
async def get_detector(
    request: Request,
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
):
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "input_coordinates": {
                "lat1": lat1, "lon1": lon1,
                "lat2": lat2, "lon2": lon2
            },
            "detection_results": {
                "objects_found": 3,
                "metrics": {
                    "precision": 0.95,
                    "recall": 0.87,
                    "f1_score": 0.91
                }
            }
        })
    
    # Получаем изображение
    width = abs(lon2 - lon1)
    height = abs(lat2 - lat1)
    img = sat_img_service.get_image(lat1, lon1, width, height)
    
    # Конвертируем изображение для отображения
    img = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    
    # Здесь будет логика детектора
    # Пока просто рисуем тестовую рамку
    cv2.rectangle(img, (100, 100), (200, 200), (0, 255, 0), 2)
    
    # Кодируем изображение для отображения
    ret, buffer = cv2.imencode('.jpg', img)
    encoded_img = base64.b64encode(buffer.tobytes()).decode('utf-8')
    
    return templates.TemplateResponse("detector.html", {
        "request": request,
        "active_page": "test",
        "coordinates": {
            "lat1": lat1, "lon1": lon1,
            "lat2": lat2, "lon2": lon2
        },
        "encoded_img": encoded_img,
        "metrics": {
            "precision": 0.95,
            "recall": 0.87,
            "f1_score": 0.91
        }
    })

# Добавим новые эндпоинты для работы с сервисами
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
