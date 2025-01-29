#Обобщенный класс работы со спутниковыми сервисами
from nasa import NASAAPI
from SentinelHub import SentinelHubAPI
from datetime import datetime
#Спутниковые сервисы
sat_services = [ NASAAPI, SentinelHubAPI]

class Image_service:
    def __init__(self):
        self.services = sat_services
        self.active_service = None
    #Получаем список сервисов, доступных для работы
    def get_services(self):
        return [name for name in self.services]
    #Задание текущего сервиса для работы
    def Set_active_service(self, id):
        self.active_service = self.services[id]
        return self.active_service

    def get_image(self, latitude, longitude, angle_width = 0.05, angle_height = 0.05, time = None):
        if time is None:
            time = datetime.now()
        return self.active_service.fetch_image(latitude, longitude, angle_width, angle_height,time)