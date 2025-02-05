from pydantic import BaseModel
from datetime import datetime

# Модели данных
class Email(BaseModel):
    email: str

class Region(BaseModel):
    name: str
    lat1: float
    lon1: float
    lat2: float
    lon2: float

class Detection(BaseModel):
    lat1: float
    lon1: float
    lat2: float
    lon2: float
    name: str
    id: int
    time: datetime
    score: float

# Временное хранилище данных (в реальном приложении использовать базу данных)
class InmemoryRepository:
    def __init__(self):
        self.emails = []  # список адресов для уведомлений
        self.regions = []  # список регионов для сканирования
        self.detections = []  # список обнаруженных объектов
    def get_emails(self):
        return self.emails
    def get_regions(self):
        return self.regions
    def add_email(self, email):
        self.emails.append(email)
        return len(self.emails) - 1
    def add_region(self, region):
        self.regions.append(region)
        return len(self.regions) - 1
    def remove_email(self, email_id:int):
        if email_id >= len(self.emails):
            raise IndexError(f'No email with id {email_id}')
        del self.emails[email_id]
    def remove_region(self, region_id:int):
        if region_id >= len(self.regions):
            raise IndexError(f'No region with id {region_id}')
        del self.regions[region_id]
    def add_detection(self, detection:Detection):
        self.detections.append(detection)
    def get_detections(self, start_time:datetime, end_time:datetime):
        return [detection for detection in self.detections if detection.time >= start_time and detection.time <= end_time]
    def get_all_detections(self):
        return self.detections
    def del_detection(self, detection_id:int):
        if detection_id >= len(self.detections):
            raise IndexError(f'No detection with id {detection_id}')
        del self.detections[detection_id]

wildfire_params_repository = InmemoryRepository()