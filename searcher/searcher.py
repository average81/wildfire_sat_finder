#Модуль поиска объектов в заданной области
from sat_service.sat_service import sat_img_service
from detector.detector import obj_detector
from repository.repository import wildfire_params_repository
import time
import threading
import numpy as np

class Object_Searcher:
    def __init__(self):
        self.regions = []
        self.stop = False
    def search_area_update(self):
        self.regions = wildfire_params_repository.get_regions()
    def search_thread(self):
        while self.stop == False:
            regions = self.regions
            print('start search')
            for region in regions:
                print(region)
                #Разбиваем область на квадраты по 0.015 градуса
                for lat in range(int((region['lat2'] - region['lat1']) / 0.015)):
                    for lon in range(int((region['lon2'] - region['lon1']) / 0.015)):
                        # Получаем изображение через сервис
                        cur_lat = region['lat1'] + lat * 0.015
                        cur_lon = region['lon1'] + lon * 0.015
                        img = sat_img_service.get_image(cur_lat, cur_lon, 0.015, 0.015)
                        if img:
                            # Конвертируем изображение из PIL в формат для отображения
                            img2 = np.array(img.convert("RGB"))
                            #Детектируем аномалии
                            prediction = obj_detector.detect(img2)
                            if len(prediction) > 0:
                                for pred in prediction:
                                    #Тут в дальнейшем будем писать в базу данных
                                    print(f"В квадрате {cur_lat}, {cur_lon}, {cur_lat + 0.015}, {cur_lon + 0.015} "
                                          f"найден объект {pred['type_name']}, вероятность {pred['score']}")
            # Выдерживаем паузу в сутки
            time.sleep(60)

fire_searcher = Object_Searcher()
t = threading.Thread(target= fire_searcher.search_thread)
t.start()  # Запустили поток
