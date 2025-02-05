from detector.roboflow_detector import roboflowdet
from pydantic import BaseModel

#Описание параметров детектора
class DetectorSettings(BaseModel):
    score_threshold: float
    min_area: float
# Список реализованных детекторов (пока только одна модель)
detectors = [roboflowdet]
# Объект детектора, обертка над моделями ИИ для унификации интерфейса
class Anomaly_detector:
    def __init__(self):
        self.model = detectors[0]
        self.model.confidence = 0.02
        self.model.min_area = 0
    # Получение списка моделей
    def get_models(self):
        return [det.get_model_name() for det in detectors]
    # Установка модели для текущей работы
    def set_model(self, id):
        if id >= len(detectors):
            raise Exception("Model not found")
        self.model = detectors[id]
    # Обработка изображения
    def detect(self, image):
        return self.model.detect(image)

obj_detector = Anomaly_detector()