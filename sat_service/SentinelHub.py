from sentinelhub import (
    BBox,
    CRS,
    DataCollection,
    MimeType,
    SentinelHubRequest,
    SHConfig,
)
import PIL
import PIL.Image
from datetime import datetime, timedelta
import numpy as np

class SentinelHubAPI:
    """
    Класс для взаимодействия с Sentinel Hub API для получения спутниковых изображений.
    """

    def __init__(self, client_id: str = '5ddcc634-6035-4849-bcfd-387cd1e5795c', client_secret: str = 'XdyrnyOkCQfaYn9Lqa0M70fB9HvxUdT8'):
        """
        Инициализирует экземпляр SentinelHubAPI с заданными учетными данными.

        Args:
            client_id (str): Client ID для Sentinel Hub.
            client_secret (str): Client Secret для Sentinel Hub.
        """
        self.name = "SentinelHub"
        try:
            self.config = SHConfig()
            self.config.sh_client_id = client_id
            self.config.sh_client_secret = client_secret

            if not self.config.sh_client_id or not self.config.sh_client_secret:
                raise ValueError("Необходимо указать Client ID и Client Secret для Sentinel Hub.")
        except Exception as e:
            raise ValueError(f"Ошибка инициализации SentinelHubAPI: {str(e)}") from e

    def fetch_image(
            self,
            lat: float,
            lon: float,
            delta_lat: float,
            delta_lon: float,
            end_date: datetime
    ) -> PIL.Image.Image:
        """
        Получает изображение с Sentinel Hub API по заданным параметрам.

        Args:
            lat (float): Широта центра области.
            lon (float): Долгота центра области.

            end_date (datetime): Конечная дата.
            delta_lon (float): Дельта долготы для области.
            delta_lat (float): Дельта широты для области.

        Returns:
            PIL.Image.Image: Полученное изображение.

        Raises:
            ValueError: Если изображение не может быть загружено или обработано.
        """
        try:
            # Вычисляем границы области
            bbox = BBox(
                (lon - delta_lon, lat - delta_lat, lon + delta_lon, lat + delta_lat),
                CRS.WGS84
            )
            size = (700, 700)  # Размер изображения
            start_date = end_date - timedelta(days=20)
            time_interval = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))  # Временной интервал

            # Скрипт для получения цветного изображения
            evalscript_true_color = """
            //VERSION=3

            function setup() {
                return {
                    input: [{
                        bands: ["B02", "B03", "B04"]
                    }],
                    output: {
                        bands: 3
                    }
                };
            }

            function evaluatePixel(sample) {
                return [sample.B04, sample.B03, sample.B02];
            }
            """

            # Создаем запрос к Sentinel Hub
            request = SentinelHubRequest(
                evalscript=evalscript_true_color,
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=DataCollection.SENTINEL2_L2A,
                        time_interval=time_interval,
                    )
                ],
                responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
                bbox=bbox,
                size=size,
                config=self.config,
            )

            # Получаем данные
            data = request.get_data()
            if data:
                image = data[0]
                return PIL.Image.fromarray(np.uint8(image))
            else:
                raise ValueError("Не удалось загрузить изображение из Sentinel Hub")
        except Exception as e:
            raise ValueError(f"Ошибка получения изображения из Sentinel Hub: {str(e)}") from e

    #Настройка параметров
    def set_params(self, *args):
        self.config.sh_client_id = args[1]
        self.config.sh_client_secret = args[0]
sentinelsat = SentinelHubAPI()