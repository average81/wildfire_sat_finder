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
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Управление email адресами
@app.get("/emails", response_class=HTMLResponse)
async def get_emails_page(request: Request):
    return templates.TemplateResponse("emails.html", {"request": request})

@app.get("/emails/list")
async def get_emails():
    return JSONResponse(content=emails)

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
@app.get("/regions", response_class=HTMLResponse)
async def get_regions_page(request: Request):
    return templates.TemplateResponse("regions.html", {"request": request})

@app.get("/regions/list")
async def get_regions():
    return JSONResponse(content=regions)

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
async def get_area_image(lat1: float, lon1: float, lat2: float, lon2: float, width: int, height: int):
    # Здесь будет логика получения изображения
    return {"message": "Image retrieval not implemented yet"}

@app.get("/tstimage", response_class=HTMLResponse)
async def test_page(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})

@app.post("/tstimage")
async def upload_test_image(file: UploadFile = File(...)):
    # Здесь будет логика сохранения тестового изображения
    return {"filename": file.filename}

@app.get("/tstdetect")
async def test_detect():
    # Здесь будет логика работы детектора
    return {"message": "Detection not implemented yet"}

@app.get("/areamap/{region_id}")
async def get_area_map(region_id: int):
    if region_id not in regions:
        raise HTTPException(status_code=404, detail="Region not found")
    # Здесь будет логика получения карты с аномалиями
    return {"message": "Area map retrieval not implemented yet"}

# Настройка модулей
@app.put("/sat_service")
async def configure_sat_service(settings: SatServiceSettings):
    # Здесь будет логика настройки сервиса спутниковых снимков
    return settings

@app.put("/detector")
async def configure_detector(settings: DetectorSettings):
    # Здесь будет логика настройки детектора
    return settings
