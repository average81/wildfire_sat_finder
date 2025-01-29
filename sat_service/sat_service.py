#Обобщенный класс работы со спутниковыми сервисами
from sat_service.nasa import nasasat
from sat_service.SentinelHub import sentinelsat
from datetime import datetime
#Спутниковые сервисы
sat_services = [ nasasat, sentinelsat]

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
        return self.active_service.fetch_image(latitude, longitude, angle_width, angle_height,time)

sat_img_service = Image_service()