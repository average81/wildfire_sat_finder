from roboflow_detector import roboflowdet

detectors = [roboflowdet]

class Anomaly_detector:
    def __init__(self):
        self.model = detectors[0]
        self.model.confidence = 0.25

    def get_models(self):
        return [det.get_model_name() for det in detectors]

    def set_model(self, id):
        if id >= len(detectors):
            raise Exception("Model not found")
        self.model = detectors[id]

    def detect(self, image):
        return self.model.detect(image)