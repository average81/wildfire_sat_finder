#Модуль поиска объектов в заданной области
from sat_service.sat_service import sat_img_service
from detector.detector import obj_detector
from repository.repository import wildfire_params_repository
import time

class Object_Searcher:
    def __init__(self):
        self.regions = None
    def search_area_update(self):
        self.regions = wildfire_params_repository.get_regions()
    def search_thread(self):
        for region in self.regions:
            #Разбиваем область на квадраты по 0.015 градуса
            for lat in range(int((region['lat2'] - region['lat1']) / 0.015)):
                for lon in range(int((region['lon2'] - region['lon1']) / 0.015)):
                    # Получаем изображение через сервис
                    img = sat_img_service.get_image(lat, lon, 0.015, 0.015)
                    if img:
                        # Конвертируем изображение из PIL в формат для отображения
                        img2 = np.array(img.convert("RGB"))
                        #Детектируем аномалии
                        prediction = obj_detector.detect(img2)
                        if len(prediction) > 0:
                            for pred in prediction:
                                #Тут в дальнейшем будем писать в базу данных
                                print(f"В квадрате {lat}, {lon}, {lat + 0.015}, {lon + 0.015} найден объект {pred['type_name']}")
        # Выдерживаем паузу в сутки
        time.sleep(24 * 60 * 60)