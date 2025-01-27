# Используем официальный Python образ с фиксированной версией для стабильности
FROM python:3.9-slim-buster

# Устанавливаем системные зависимости для OpenCV и других библиотек
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию и переходим в нее
WORKDIR /app

# Сначала копируем только requirements.txt для кэширования слоя с зависимостями
COPY requirements.txt .

# Устанавливаем Python зависимости с фиксацией версий
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir protobuf==3.20.3  # Явная фиксация версии для совместимости

# Копируем все файлы приложения
COPY . .

# Экспонируем порт Streamlit
EXPOSE 8501

# Запускаем приложение с оптимальными настройками для контейнера
CMD ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.enableCORS=false", \
    "--server.enableXsrfProtection=false"]