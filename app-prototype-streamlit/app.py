import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import PIL
import requests
import streamlit as st
import tempfile

from datetime import date
from io import BytesIO
from sentinelhub import (
    BBox,
    CRS,
    DataCollection,
    MimeType,
    SentinelHubRequest,
    SHConfig,
)
from typing import Any, Dict, Tuple, Union
from inference_sdk import InferenceHTTPClient

# Константы для приложения
NASA_API_URL = "https://api.nasa.gov/planetary/earth/imagery"
ROBOFLOW_MODEL_ID = "wildfire-tksrf/2"
IMAGE_FORMATS = ("jpg", "jpeg", "png", "bmp", "tiff")


def configure_app():
    """
    Инициализирует параметры страницы Streamlit, такие как заголовок,
    иконка, макет и начальное состояние боковой панели.
    """
    st.set_page_config(
        page_title="Fire Detection PRO",
        page_icon="🔥",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("🔥 Система детекции лесных пожаров")
    st.caption("Проект для TSU CV 2025 | Только Roboflow модель")


@st.cache_resource(show_spinner="Инициализация AI модели...")
def load_model() -> InferenceHTTPClient:
    """
    Загружает и инициализирует клиент модели Roboflow.

    Returns:
        InferenceHTTPClient: Клиент для выполнения инференса.

    Raises:
        RuntimeError: Если инициализация клиента модели не удалась.
    """
    try:
        client = InferenceHTTPClient(
            api_url="https://detect.roboflow.com",
            api_key="2UgAsIW11EHQmt8gh36L"
        )
        return client
    except Exception as e:
        st.error(f"🚨 Критическая ошибка инициализации модели: {str(e)}")
        st.stop()


def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """
    Проверяет, находятся ли координаты в допустимом диапазоне.

    Args:
        lat (float): Широта.
        lon (float): Долгота.

    Returns:
        Tuple[bool, str]: Tuple, где первый элемент указывает валидность,
                          а второй содержит сообщение об ошибке при необходимости.
    """
    if not (-90 <= lat <= 90):
        return False, "❌ Широта должна быть в диапазоне -90 до 90"
    if not (-180 <= lon <= 180):
        return False, "❌ Долгота должна быть в диапазоне -180 до 180"
    return True, ""


def convert_image(image: Union[PIL.Image.Image, np.ndarray, bytes]) -> np.ndarray:
    """
    Конвертирует различные типы изображений в формат numpy ndarray.

    Args:
        image (Union[PIL.Image.Image, np.ndarray, bytes]): Входное изображение.

    Returns:
        np.ndarray: Конвертированное изображение в формате BGR.

    Raises:
        ValueError: Если конвертация изображения не удалась.
    """
    try:
        if isinstance(image, PIL.Image.Image):
            # Преобразуем PIL Image в формат, совместимый с OpenCV (BGR)
            return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        if isinstance(image, bytes):
            # Декодируем изображение из байтового потока
            return cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        if isinstance(image, np.ndarray):
            # Убедимся, что изображение в формате BGR
            if image.ndim == 3 and image.shape[2] == 3:
                return image.copy()
            else:
                raise ValueError("Неверный формат изображения")
        raise ValueError("Неизвестный тип изображения")
    except Exception as e:
        raise ValueError(f"Ошибка конвертации изображения: {str(e)}") from e


class NASAAPI:
    """
    Класс для взаимодействия с NASA API с целью получения спутниковых изображений.
    """

    def __init__(self, api_key: str):
        """
        Инициализирует экземпляр NASAAPI с заданным API ключом.

        Args:
            api_key (str): Ключ API для доступа к NASA API.
        """
        self.api_key = api_key

    def fetch_image(self, lat: float, lon: float, date_str: str) -> PIL.Image.Image:
        """
        Получает изображение с NASA API по заданным координатам и дате.

        Args:
            lat (float): Широта.
            lon (float): Долгота.
            date_str (str): Дата в формате 'YYYY-MM-DD'.

        Returns:
            PIL.Image.Image: Полученное изображение.

        Raises:
            requests.HTTPError: Если запрос к NASA API завершился ошибкой.
            ValueError: Если изображение не может быть обработано.
        """
        params = {
            'lat': lat,
            'lon': lon,
            'date': date_str,
            'dim': 0.05,  # Размер области в градусах
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


class SentinelHubAPI:
    """
    Класс для взаимодействия с Sentinel Hub API для получения спутниковых изображений.
    """

    def __init__(self, client_id: str, client_secret: str):
        """
        Инициализирует экземпляр SentinelHubAPI с заданными учетными данными.

        Args:
            client_id (str): Client ID для Sentinel Hub.
            client_secret (str): Client Secret для Sentinel Hub.
        """
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
        start_date: str,
        end_date: str,
        delta_lon: float,
        delta_lat: float
    ) -> PIL.Image.Image:
        """
        Получает изображение с Sentinel Hub API по заданным параметрам.

        Args:
            lat (float): Широта центра области.
            lon (float): Долгота центра области.
            start_date (str): Начальная дата в формате 'YYYY-MM-DD'.
            end_date (str): Конечная дата в формате 'YYYY-MM-DD'.
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
            time_interval = (start_date, end_date)  # Временной интервал

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


class FileHandler:
    """
    Класс для обработки загруженных пользователем файлов.
    """

    def __init__(self):
        """
        Инициализация FileHandler. В текущей реализации нет параметров.
        """
        pass

    def upload_file(self, uploaded_file: bytes) -> np.ndarray:
        """
        Обрабатывает загруженный файл и преобразует его в формат numpy массива.

        Args:
            uploaded_file (bytes): Байтовое содержимое загруженного файла.

        Returns:
            np.ndarray: Обработанное изображение в формате BGR.

        Raises:
            ValueError: Если обработка файла не удалась.
        """
        try:
            image = PIL.Image.open(BytesIO(uploaded_file))
            return convert_image(image)
        except Exception as e:
            raise ValueError(f"Ошибка обработки файла: {str(e)}") from e


class ImageProcessor:
    """
    Класс для обработки изображений и интеграции с моделью инференса.
    """

    def __init__(self, model: InferenceHTTPClient):
        """
        Инициализирует обработчик изображений с моделью инференса.

        Args:
            model (InferenceHTTPClient): Клиент модели для инференса.
        """
        self.model = model
        self.confidence = 0.25  # Стандартный порог уверенности

    def process_uploaded_file(self, uploaded_file: Union[PIL.Image.Image, bytes]) -> Union[np.ndarray, None]:
        """
        Обрабатывает загруженный файл и преобразует его в numpy массив.

        Args:
            uploaded_file (Union[PIL.Image.Image, bytes]): Загруженный файл.

        Returns:
            Union[np.ndarray, None]: Обработанное изображение или None при ошибке.
        """
        try:
            return convert_image(uploaded_file)
        except Exception as e:
            st.error(f"📁 Ошибка обработки файла: {str(e)}")
            return None

    def run_inference(self, image: np.ndarray) -> Dict[str, Any]:
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
            with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
                # Сохраняем изображение во временный файл
                cv2.imwrite(tmp.name, image)
                # Запускаем инференс
                result = self.model.infer(tmp.name, model_id=ROBOFLOW_MODEL_ID)
                if not result:
                    raise ValueError("Результат инференса пустой")
                return {
                    "predictions": result.get("predictions", []),
                    "time": result.get("time", 0),
                    "width": image.shape[1],
                    "height": image.shape[0]
                }
        except Exception as e:
            st.error(f"🤖 Ошибка AI-инференса: {str(e)}")
            return {}


class ResultVisualizer:
    """
    Класс для визуализации результатов инференса и аналитики.
    """

    def __init__(self):
        """
        Инициализирует визуализатор с предопределенными цветами для классов.
        """
        self.class_colors = {
            "fire": (0, 0, 255),
            "smoke": (255, 0, 0),
            "Wildfire": (0, 255, 0)
        }

    def visualize(self, image: np.ndarray, detections: Dict[str, Any]) -> np.ndarray:
        """
        Визуализирует bounding boxes и метки на изображении.

        Args:
            image (np.ndarray): Исходное изображение.
            detections (Dict[str, Any]): Результаты инференса.

        Returns:
            np.ndarray: Изображение с визуализированными детекциями.
        """
        img = image.copy()
        for pred in detections.get("predictions", []):
            try:
                # Конвертация относительных координат в абсолютные
                x_center = pred["x"] * detections["width"]
                y_center = pred["y"] * detections["height"]
                width = pred["width"] * detections["width"]
                height = pred["height"] * detections["height"]

                # Вычисление верхнего левого угла
                x = int(x_center - width / 2)
                y = int(y_center - height / 2)
                w = int(width)
                h = int(height)

                # Выбор цвета на основе класса
                color = self.class_colors.get(pred["class"], (0, 0, 255))
                # Рисуем прямоугольник
                cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                # Создаем подпись
                label = f"{pred['class']} {pred['confidence']:.2f}"
                # Наносим подпись на изображение
                cv2.putText(img, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            except KeyError as e:
                st.warning(f"Недостающий ключ в предсказании: {e}")
            except Exception as e:
                st.warning(f"Ошибка визуализации предсказания: {e}")

        # Конвертируем цветовую схему обратно для отображения в Streamlit
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def show_stats(self, detections: Dict[str, Any]):
        """
        Отображает аналитику детекций, включая распределение уверенности.

        Args:
            detections (Dict[str, Any]): Результаты инференса.
        """
        stats = {"fire": 0, "smoke": 0, "Wildfire": 0}
        confidences = []

        # Подсчет количества объектов каждого класса и сбор уверенности
        for pred in detections.get("predictions", []):
            cls_name = pred.get("class")
            confidence = pred.get("confidence", 0)
            if cls_name in stats:
                stats[cls_name] += 1
                confidences.append(confidence)

        with st.expander("📊 Детальная аналитика", expanded=True):
            cols = st.columns(3)
            cols[0].metric("🔥 Пожары", stats["fire"], delta_color="off")
            cols[1].metric("💨 Дым", stats["smoke"], delta_color="off")
            cols[2].metric("🌟 Wildfire", stats["Wildfire"], delta_color="off")

            if confidences:
                st.markdown(f"**🕒 Время обработки:** {detections.get('time', 0):.2f} ms")
                plt.figure(figsize=(10, 4))
                plt.hist(confidences, bins=20, range=(0, 1), color='red', alpha=0.7)
                plt.title("Распределение уверенности модели")
                plt.xlabel("Уверенность")
                plt.ylabel("Количество обнаружений")
                st.pyplot(plt, clear_figure=True)
            else:
                st.warning("⚠️ Объекты не обнаружены")


def main():
    """
    Основная функция приложения Streamlit. Управляет интерфейсом пользователя,
    взаимодействием с API и отображением результатов.
    """
    configure_app()
    model = load_model()
    processor = ImageProcessor(model)
    visualizer = ResultVisualizer()

    # Инициализация состояния сессии
    if "nasa_image" not in st.session_state:
        st.session_state.nasa_image = None
    if "sentinelhub_image" not in st.session_state:
        st.session_state.sentinelhub_image = None
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None

    # Конфигурация панели управления
    with st.sidebar:
        st.header("⚙️ Настройки")
        processor.confidence = st.slider(
            "Порог уверенности",
            0.0, 1.0, 0.25, 0.05,
            help="Регулировка чувствительности детекции модели."
        )

        st.header("🌍 Источник данных")
        source = st.radio(
            "Выберите источник:",
            ["📁 Файл", "🛰️ NASA API", "🛰️ Sentinel Hub API"],
            index=0
        )

        # Обработка источника "🛰️ NASA API"
        if source == "🛰️ NASA API":
            api_key = st.text_input(
                "Ключ NASA API",
                type="password",
                value='uquMPkqqugLLa51krBVA3bRHlb5M6IZg2SrJkKiE',
                help="Получить ключ: https://api.nasa.gov"
            )

            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input("Широта", -90.0, 90.0, 39.2106, format="%.6f")
            with col2:
                lon = st.number_input("Долгота", -180.0, 180.0, -121.6701, format="%.6f")

            selected_date = st.date_input(
                "Дата съемки",
                date(2019, 1, 2),
                min_value=date(2017, 1, 1)
            )

            if st.button("🌐 Загрузить со спутника"):
                valid, msg = validate_coordinates(lat, lon)
                if not valid:
                    st.error(msg)
                    st.stop()

                try:
                    # Инициализируем класс NASAAPI с введенным ключом
                    nasa_api = NASAAPI(api_key)
                    # Получаем изображение по заданным параметрам
                    st.session_state.nasa_image = nasa_api.fetch_image(
                        lat,
                        lon,
                        selected_date.isoformat()
                    )
                    st.toast("✅ Спутниковые данные успешно загружены", icon="🛰️")
                except Exception as e:
                    st.error(f"❌ Ошибка загрузки: {str(e)}")

        # Обработка источника "🛰️ Sentinel Hub API"
        elif source == "🛰️ Sentinel Hub API":
            st.subheader("Настройки Sentinel Hub")
            client_id = st.text_input(
                "Client ID",
                type="password",
                value='5ddcc634-6035-4849-bcfd-387cd1e5795c',
                help="Введите ваш Sentinel Hub Client ID"
            )
            client_secret = st.text_input(
                "Client Secret",
                type="password",
                value='XdyrnyOkCQfaYn9Lqa0M70fB9HvxUdT8',
                help="Введите ваш Sentinel Hub Client Secret"
            )

            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input("Широта", -90.0, 90.0, 39.2106, format="%.6f")
            with col2:
                lon = st.number_input("Долгота", -180.0, 180.0, -121.6701, format="%.6f")

            date_col1, date_col2 = st.columns(2)
            with date_col1:
                start_date = st.date_input(
                    "Дата начала",
                    date(2019, 1, 2),
                    min_value=date(2015, 6, 23)
                )
            with date_col2:
                end_date = st.date_input(
                    "Дата конца",
                    date(2019, 1, 3),
                    min_value=start_date
                )

            delta_col1, delta_col2 = st.columns(2)
            with delta_col1:
                delta_lon = st.number_input(
                    "Дельта долготы",
                    0.01, 5.0, 0.5, format="%.3f",
                    help="Определяет размер области по долготе"
                )
            with delta_col2:
                delta_lat = st.number_input(
                    "Дельта широты",
                    0.01, 5.0, 0.4, format="%.3f",
                    help="Определяет размер области по широте"
                )

            if st.button("🌐 Загрузить изображение Sentinel Hub"):
                valid, msg = validate_coordinates(lat, lon)
                if not valid:
                    st.error(msg)
                    st.stop()

                try:
                    # Инициализируем класс SentinelHubAPI с введенными учетными данными
                    sentinel_api = SentinelHubAPI(client_id, client_secret)
                    # Получаем изображение по заданным параметрам
                    st.session_state.sentinelhub_image = sentinel_api.fetch_image(
                        lat,
                        lon,
                        start_date.isoformat(),
                        end_date.isoformat(),
                        delta_lon,
                        delta_lat
                    )
                    st.toast("✅ Изображение Sentinel Hub успешно загружено", icon="🛰️")
                except Exception as e:
                    st.error(f"❌ Ошибка загрузки изображения из Sentinel Hub: {str(e)}")

        # Обработка источника "📁 Файл"
        else:
            file_handler = FileHandler()
            uploaded_file = st.file_uploader(
                "Загрузите изображение...",
                type=IMAGE_FORMATS,
                help="Поддерживаемые форматы: " + ", ".join(IMAGE_FORMATS)
            )
            if uploaded_file:
                try:
                    # Обрабатываем загруженный файл
                    st.session_state.uploaded_image = uploaded_file.read()
                    st.success("📂 Файл успешно загружен")
                except Exception as e:
                    st.error(f"❌ Ошибка загрузки файла: {str(e)}")

    # Основной интерфейс отображения изображений
    col1, col2 = st.columns(2)

    with col1:
        if source == "🛰️ NASA API" and st.session_state.nasa_image:
            st.image(
                st.session_state.nasa_image,
                caption=f"📍 Координаты: {lat:.4f}, {lon:.4f} | 📅 {selected_date}",
                use_column_width=True
            )
        elif source == "📁 Файл" and st.session_state.uploaded_image:
            # Конвертируем байты в изображение для отображения
            try:
                uploaded_image = PIL.Image.open(BytesIO(st.session_state.uploaded_image))
                st.image(
                    uploaded_image,
                    caption="Загруженное изображение",
                    use_column_width=True
                )
            except Exception as e:
                st.error(f"❌ Ошибка отображения изображения: {str(e)}")
        elif source == "🛰️ Sentinel Hub API" and st.session_state.sentinelhub_image:
            st.image(
                st.session_state.sentinelhub_image,
                caption=f"📍 Координаты: {lat:.4f}, {lon:.4f} | 📅 {start_date} - {end_date}",
                use_column_width=True
            )

    # Кнопка запуска анализа изображения
    if st.sidebar.button("🚀 Запустить анализ", type="primary"):
        # Проверка наличия загруженного изображения в зависимости от источника
        if (source == "🛰️ NASA API" and not st.session_state.nasa_image) or \
           (source == "📁 Файл" and not st.session_state.uploaded_image) or \
           (source == "🛰️ Sentinel Hub API" and not st.session_state.sentinelhub_image):
            st.warning("⚠️ Сначала загрузите изображение")
            st.stop()

        try:
            with st.spinner("🔍 Анализ изображения..."):
                # Определение источника изображения
                if source == "🛰️ NASA API":
                    image_data = st.session_state.nasa_image
                elif source == "🛰️ Sentinel Hub API":
                    image_data = st.session_state.sentinelhub_image
                elif source == "📁 Файл":
                    image_data = st.session_state.uploaded_image
                else:
                    st.error("❌ Неизвестный источник данных")
                    st.stop()

                # Конвертируем изображение в формат numpy массива
                if source == "📁 Файл":
                    image = processor.upload_file(image_data)
                else:
                    image = convert_image(image_data)

                # Запускаем инференс модели
                detections = processor.run_inference(image)
                if not detections:
                    st.error("❌ Не удалось получить результаты инференса")
                    st.stop()

                # Добавляем размеры изображения в результаты
                detections.update({
                    "width": image.shape[1],
                    "height": image.shape[0]
                })

                # Визуализируем результаты на изображении
                visualized = visualizer.visualize(image, detections)
                col2.image(
                    visualized,
                    caption="Результаты компьютерного зрения",
                    use_column_width=True
                )

                # Отображаем аналитику
                visualizer.show_stats(detections)

        except Exception as e:
            st.error(f"⛔ Критическая ошибка: {str(e)}")
            st.exception(e)


if __name__ == "__main__":
    main()