from inference_sdk import InferenceHTTPClient
from typing import Any, Dict, Tuple, Union
import numpy as np
import tempfile
from PIL import Image

client = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="2UgAsIW11EHQmt8gh36L"
)
roboflow_models = [
    {'name': 'Roboflow 3.0 Object Detection (Fast)', 'model_id': "wildfire-tksrf/2"}
]

class RoboFlow_detector:
    """
    Класс для обработки изображений и интеграции с моделью инференса.
    """

    def __init__(self):
        """
        Инициализирует обработчик изображений с моделью инференса.

        Args:
            model (InferenceHTTPClient): Клиент модели для инференса.
        """
        self.client = client
        self.model_num = 0
        self.confidence = 0.2  # Стандартный порог уверенности

    def get_model_name(self):
        return roboflow_models[self.model_num]["name"]

    def detect(self, image: np.ndarray):
        """
        Запускает инференс модели на заданном изображении.

        Args:
            image (np.ndarray): Изображение для анализа.

        Returns:
            Dict[str, Any]: Результаты инференса.

        Raises:
            ValueError: Если инференс не удался или результаты некорректны.
        """
        try:
            pil_image = Image.fromarray(image)
            pil_image.save('tmp.jpg')
            # Запускаем инференс
            result = self.client.infer('tmp.jpg', model_id=roboflow_models[self.model_num]["model_id"])
            #print(result)
            if not result:
                return []
            ret = []
            for i,pred in zip(range(0,len(result.get("predictions", []))),result.get("predictions", [])):
                # Вычисление верхнего левого угла
                x1 = int(pred["x"] - pred["width"] / 2)
                y1 = int(pred["y"] - pred["height"] / 2)
                x2 = int(pred["x"] + pred["width"] / 2)
                y2 = int(pred["y"] + pred["height"] / 2)
                if pred['confidence'] >= self.confidence:
                    ret.append({'type_name': pred['class'], 'type_id': i, 'score': pred['confidence'], 'box': [x1, y1, x2, y2]})
            return ret

        except Exception as e:
            print(e)
            return []
roboflowdet = RoboFlow_detector()