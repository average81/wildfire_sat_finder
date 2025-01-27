import PIL
import cv2
import numpy as np
import streamlit as st
import tempfile
import requests
from io import BytesIO
from datetime import date
from inference_sdk import InferenceHTTPClient
from typing import Union, Tuple, Dict, Any
import matplotlib.pyplot as plt

# Константы
NASA_API_URL = "https://api.nasa.gov/planetary/earth/imagery"
ROBOFLOW_MODEL_ID = "wildfire-tksrf/2"
IMAGE_FORMATS = ("jpg", "jpeg", "png", "bmp", "tiff")

def configure_app():
    """Инициализация параметров Streamlit"""
    st.set_page_config(
        page_title="Fire Detection PRO",
        page_icon="🔥",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("🔥 Система детекции лесных пожаров")
    st.caption("Проект для TSU CV 2025 | Только Roboflow модель")

@st.cache_resource(show_spinner="Инициализация AI модели...")
def load_model():
    """Загрузка и валидация Roboflow модели"""
    try:
        client = InferenceHTTPClient(
            api_url="https://detect.roboflow.com",
            api_key="2UgAsIW11EHQmt8gh36L"
        )
        #TODO: Тестовый запрос для проверки работоспособности API, не работает
        # можно добавить но в последний момент задачи very low
        #client.infer("hhttps://detect.roboflow.com", model_id=ROBOFLOW_MODEL_ID)
        return client
    except Exception as e:
        st.error(f"🚨 Критическая ошибка инициализации модели: {str(e)}")
        st.stop()

def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """Валидация географических координат"""
    if not (-90 <= lat <= 90):
        return False, "❌ Широта должна быть в диапазоне -90 до 90"
    if not (-180 <= lon <= 180):
        return False, "❌ Долгота должна быть в диапазоне -180 до 180"
    return True, ""

def convert_image(image: Union[PIL.Image.Image, np.ndarray, bytes]) -> np.ndarray:
    """Конвертация изображений с обработкой исключений"""
    try:
        if isinstance(image, PIL.Image.Image):
            return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        if isinstance(image, bytes):
            return cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        return image.copy()
    except Exception as e:
        raise ValueError(f"Ошибка конвертации изображения: {str(e)}")

class ImageProcessor:
    """Обработчик изображений с интеграцией Roboflow"""
    def __init__(self, model):
        self.model = model
        self.confidence = 0.25  # Стандартное значение уверенности
        
    def process_uploaded_file(self, uploaded_file: Union[PIL.Image.Image, bytes]) -> Union[np.ndarray, None]:
        """Обработка файлов с диагностикой"""
        try:
            return convert_image(uploaded_file)
        except Exception as e:
            st.error(f"📁 Ошибка обработки файла: {str(e)}")
            return None
        
    def run_inference(self, image: np.ndarray) -> Dict[str, Any]:
        """Оптимизированный инференс с таймингом и обработкой ошибок"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
                cv2.imwrite(tmp.name, image)
                result = self.model.infer(tmp.name, 
                                        model_id=ROBOFLOW_MODEL_ID)
                return {
                    "predictions": result.get("predictions", []),
                    "time": result.get("time", 0),
                    "width": image.shape[1],
                    "height": image.shape[0]
                }
        except Exception as e:
            st.error(f"🤖 Ошибка AI-инференса: {str(e)}")
            return None

class ResultVisualizer:
    """Визуализация результатов с аналитикой"""
    def __init__(self):
        self.class_colors = {
            "fire": (0, 0, 255),
            "smoke": (255, 0, 0),
            "Wildfire": (0, 255, 0)
        }
        
    def visualize(self, image: np.ndarray, detections: Dict[str, Any]) -> np.ndarray:
        """Точное позиционирование bounding boxes с учетом размеров изображения"""
        #TODO: Исправить не выводит бокс
        img = image.copy()
        for pred in detections.get("predictions", []):
            print(pred)
            # Конвертация относительных координат в абсолютные
            x_center = pred["x"] * detections["width"]
            y_center = pred["y"] * detections["height"]
            width = pred["width"] * detections["width"]
            height = pred["height"] * detections["height"]
            
            x = int(x_center - width/2)
            y = int(y_center - height/2)
            w = int(width)
            h = int(height)
            
            color = self.class_colors.get(pred["class"], (0, 0, 255))
            cv2.rectangle(img, (x, y), (x+w, y+h), color, 2)
            label = f"{pred['class']} {pred['confidence']:.2f}"
            cv2.putText(img, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def show_stats(self, detections: Dict[str, Any]):
        """Расширенная аналитика с тепловой картой уверенности
           здесь можно добавить дополнительную аналитику 
        """
        stats = {"fire": 0, "smoke": 0, "Wildfire": 0}
        confidences = []
        
        for pred in detections.get("predictions", []):
            cls_name = pred["class"]
            if cls_name in stats:
                stats[cls_name] += 1
                confidences.append(pred["confidence"])
        
        with st.expander("📊 Детальная аналитика", expanded=True):
            cols = st.columns(3)
            cols[0].metric("💨 Модель 1", stats["fire"], delta_color="off")
            cols[1].metric("💨 Модель 2", stats["smoke"], delta_color="off")
            cols[2].metric("🔥 Пожары модель Wildfire", stats["Wildfire"], delta_color="off")
            
            if confidences:
                st.markdown(f"**🕒 Время обработки:** {detections.get('time', 0):.2f} ms")
                plt.figure(figsize=(10,4))
                plt.hist(confidences, bins=20, range=(0,1), color='red', alpha=0.7)
                plt.title("Распределение уверенности модели")
                plt.xlabel("Уверенность")
                plt.ylabel("Количество обнаружений")
                st.pyplot(plt, clear_figure=True)
            else:
                st.warning("⚠️ Объекты не обнаружены")

def main():
    configure_app()
    model = load_model()
    processor = ImageProcessor(model)
    visualizer = ResultVisualizer()
    
    # Инициализация состояния сессии
    session = st.session_state
    if "nasa_image" not in session:
        session.nasa_image = None
    
    # Конфигурация панели управления
    with st.sidebar:
        st.header("⚙️ Настройки")
        processor.confidence = st.slider("Порог уверенности", 0.0, 1.0, 0.25, 0.05,
                                       help="Регулировка чувствительности детекции модели /n * Только для локальных моделей добавлены будут позже /n Сейчас не работает")
        
        st.header("🌍 Источник данных")
        source = st.radio("Выберите источник:", ["📁 Файл", "🛰️ NASA API"], index=0)
        
        if source == "🛰️ NASA API":
            api_key = st.text_input("Ключ NASA API", type="password", 
                                  value='uquMPkqqugLLa51krBVA3bRHlb5M6IZg2SrJkKiE',
                                  help="Получить ключ: https://api.nasa.gov")
            
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input("Широта", -90.0, 90.0, 39.2106, format="%.6f")
            with col2:
                lon = st.number_input("Долгота", -180.0, 180.0, -121.6701, format="%.6f")
                
            selected_date = st.date_input("Дата съемки", date(2019, 1, 2),
                                        min_value=date(2017, 1, 1))
            
            if st.button("🌐 Загрузить со спутника"):
                valid, msg = validate_coordinates(lat, lon)
                if not valid:
                    st.error(msg)
                    return
                
                try:
                    response = requests.get(
                        NASA_API_URL,
                        params={
                            'lat': lat,
                            'lon': lon,
                            'date': selected_date.isoformat(),
                            'dim': 0.05,
                            'api_key': api_key
                        },
                        timeout=20
                    )
                    response.raise_for_status()
                    session.nasa_image = PIL.Image.open(BytesIO(response.content))
                    st.toast("✅ Спутниковые данные успешно загружены", icon="🛰️")
                except Exception as e:
                    st.error(f"❌ Ошибка загрузки: {str(e)}")
        else:
            uploaded_file = st.file_uploader("Загрузите изображение...", 
                                           type=IMAGE_FORMATS,
                                           help="Поддерживаемые форматы: " + ", ".join(IMAGE_FORMATS))
            if uploaded_file:
                session.uploaded_image = uploaded_file.read()

    # Основной интерфейс
    col1, col2 = st.columns(2)
    
    with col1:
        if source == "🛰️ NASA API" and session.nasa_image:
            st.image(session.nasa_image, 
                    caption=f"📍 Координаты: {lat:.4f}, {lon:.4f} | 📅 {selected_date}",
                    use_column_width=True)
        elif source == "📁 Файл" and "uploaded_image" in session:
            st.image(session.uploaded_image, 
                    caption="Загруженное изображение",
                    use_column_width=True)

    if st.sidebar.button("🚀 Запустить анализ", type="primary"):
        if (source == "🛰️ NASA API" and not session.nasa_image) or \
           (source == "📁 Файл" and "uploaded_image" not in session):
            st.warning("⚠️ Сначала загрузите изображение")
            return
            
        try:
            with st.spinner("🔍 Анализ изображения..."):
                image = convert_image(session.nasa_image if source == "🛰️ NASA API" 
                                    else session.uploaded_image)
                
                detections = processor.run_inference(image)
                if not detections:
                    return
                
                detections.update({
                    "width": image.shape[1],
                    "height": image.shape[0]
                })
                
                visualized = visualizer.visualize(image, detections)
                col2.image(visualized, 
                          caption="Результаты компьютерного зрения",
                          use_column_width=True)
                
                visualizer.show_stats(detections)
                
        except Exception as e:
            st.error(f"⛔ Критическая ошибка: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()