from pydantic import BaseModel

# Модели данных
class Email(BaseModel):
    email: str

class Region(BaseModel):
    name: str
    lat1: float
    lon1: float
    lat2: float
    lon2: float

# Временное хранилище данных (в реальном приложении использовать базу данных)
class InmemoryRepository:
    def __init__(self):
        self.emails = []  # список объектов
        self.regions = []  # список объектов
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

wildfire_params_repository = InmemoryRepository()