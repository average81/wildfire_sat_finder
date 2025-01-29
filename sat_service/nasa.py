import PIL
import PIL.Image
import requests
from io import BytesIO
from datetime import datetime

# Константы для приложения
NASA_API_URL = "https://api.nasa.gov/planetary/earth/imagery"
nasa_api_key = 'uquMPkqqugLLa51krBVA3bRHlb5M6IZg2SrJkKiE'

class NASAAPI:
    """
    Класс для взаимодействия с NASA API с целью получения спутниковых изображений.
    """

    def __init__(self, api_key: str = nasa_api_key):
        """
        Инициализирует экземпляр NASAAPI с заданным API ключом.

        Args:
            api_key (str): Ключ API для доступа к NASA API.
        """
        self.api_key = api_key
        self.name = 'NASA'

    def fetch_image(self, lat: float, lon: float, angle_width:float, angle_height:float,  date: datetime) -> PIL.Image.Image:
        """
        Получает изображение с NASA API по заданным координатам и дате.

        Args:
            lat (float): Широта.
            lon (float): Долгота.
            angle_width (float): Ширина области в градусах.
            angle_height (float): Высота области в градусах.
            date (datetime): Дата.

        Returns:
            PIL.Image.Image: Полученное изображение.

        Raises:
            requests.HTTPError: Если запрос к NASA API завершился ошибкой.
            ValueError: Если изображение не может быть обработано.
        """
        params = {
            'lat': lat,
            'lon': lon,
            'date': date.strftime("%YYYY-%mm-%dd"),
            'dim': min(angle_width, angle_height),  # Размер области в градусах
            'api_key': self.api_key
        }
        try:
            response = requests.get(NASA_API_URL, params=params, timeout=20)
            response.raise_for_status()  # Проверяем успешность запроса
            return PIL.Image.open(BytesIO(response.content))
        except requests.HTTPError as http_err:
            raise requests.HTTPError(f"HTTP ошибка: {http_err}") from http_err
        except Exception as e:
            raise ValueError(f"Не удалось получить или обработать изображение: {str(e)}") from e