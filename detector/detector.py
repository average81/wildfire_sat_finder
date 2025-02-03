from detector.roboflow_detector import roboflowdet
from pydantic import BaseModel


class DetectorSettings(BaseModel):
    score_threshold: float
    min_area: float

detectors = [roboflowdet]

class Anomaly_detector:
    def __init__(self):
        self.model = detectors[0]
        self.model.confidence = 0.02

    def get_models(self):
        return [det.get_model_name() for det in detectors]

    def set_model(self, id):
        if id >= len(detectors):
            raise Exception("Model not found")
        self.model = detectors[id]

    def detect(self, image):
        return self.model.detect(image)

obj_detector = Anomaly_detector()