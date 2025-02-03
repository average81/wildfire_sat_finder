#Обобщенный класс работы со спутниковыми сервисами
from sat_service.nasa import nasasat
from sat_service.SentinelHub import sentinelsat
from datetime import datetime
from typing import Any, Dict, Tuple, Union
from pydantic import BaseModel
#Спутниковые сервисы
sat_services = [ nasasat, sentinelsat]

class SatServiceSettings(BaseModel):
    api_key: str
    base_url: str
    user_id: str

def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """
    Проверяет, находятся ли координаты в допустимом диапазоне.

    Args:
        lat (float): Широта.
        lon (float): Долгота.

    Returns:
        Tuple[bool, str]: Tuple, где первый элемент указывает валидность,
                          а второй содержит сообщение об ошибке при необходимости.
    """
    if not (-90 <= lat <= 90):
        return False, "❌ Широта должна быть в диапазоне -90 до 90"
    if not (-180 <= lon <= 180):
        return False, "❌ Долгота должна быть в диапазоне -180 до 180"
    return True, ""

class Image_service:
    def __init__(self):
        self.services = sat_services
        self.active_service = sat_services[1]
    #Получаем список сервисов, доступных для работы
    def get_services(self):
        return [name for name in self.services]
    #Задание текущего сервиса для работы
    def Set_active_service(self, id):
        if id >= len(self.services):
            raise Exception('No such service')
        self.active_service = self.services[id]
        return self.active_service

    def get_image(self, latitude, longitude, angle_width = 0.05, angle_height = 0.05, time = None):
        if time is None:
            time = datetime.now()
        if self.active_service is None:
            raise Exception('No active service')
        val,err = validate_coordinates(latitude, longitude)
        if not val:
            raise Exception(err )
        return self.active_service.fetch_image(latitude, longitude, angle_width, angle_height,time)
    #Настройка параметров
    def set_params(self, settings: SatServiceSettings):
        self.active_service.set_params(settings.api_key, settings.user_id)


sat_img_service = Image_service()