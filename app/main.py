import httpx
from fastapi import FastAPI, HTTPException, Request, Response, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

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
    timeout: int

class DetectorSettings(BaseModel):
    score_threshold: float
    min_area: float

# Временное хранилище данных (в реальном приложении использовать базу данных)
emails = {}
regions = {}

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
        return JSONResponse(content=emails)
    return templates.TemplateResponse("emails.html", {"request": request, "active_page": "emails"})

@app.post("/emails/add")
async def add_email(email: Email):
    email_id = len(emails) + 1
    emails[email_id] = email.email
    return {"id": email_id, "email": email.email}

@app.delete("/emails/{email_id}")
async def delete_email(email_id: int):
    if email_id not in emails:
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
    region_id = len(regions) + 1
    regions[region_id] = region.dict()
    return {"id": region_id, "region": region}

@app.delete("/regions/{region_id}")
async def delete_region(region_id: int):
    if region_id not in regions:
        raise HTTPException(status_code=404, detail="Region not found")
    del regions[region_id]
    return {"message": "Region deleted"}

# Работа с изображениями
@app.get("/areaimg")
async def get_area_image(
    request: Request,
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float, 
    width: int, 
    height: int
):
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "coordinates": {
                "lat1": lat1, "lon1": lon1,
                "lat2": lat2, "lon2": lon2
            },
            "size": {"width": width, "height": height},
            "message": "Image retrieval not implemented yet"
        })
    # В будущем здесь будет возвращаться изображение
    return templates.TemplateResponse("image.html", {
        "request": request,
        "coordinates": {
            "lat1": lat1, "lon1": lon1,
            "lat2": lat2, "lon2": lon2
        },
        "size": {"width": width, "height": height}
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
    if region_id not in regions:
        raise HTTPException(status_code=404, detail="Region not found")
    
    if request.headers.get('Accept') == 'application/json':
        return JSONResponse(content={
            "region_id": region_id,
            "region_data": regions[region_id],
            "message": "Area map retrieval not implemented yet"
        })
    # В будущем здесь будет возвращаться HTML страница с картой
    return templates.TemplateResponse("map.html", {
        "request": request, 
        "active_page": "regions",
        "region": regions[region_id]
    })

# Настройка модулей
@app.put("/sat_service")
async def configure_sat_service(settings: SatServiceSettings):
    # Здесь будет логика настройки сервиса спутниковых снимков
    return settings

@app.put("/detector")
async def configure_detector(settings: DetectorSettings):
    # Здесь будет логика настройки детектора
    return settings
