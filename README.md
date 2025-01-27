# wildfire_sat_finder
Проект по обнаружению лесных пожаров по снимкам из космоса в рамках хакатона ТГУ.

## Установка

Для работы модели использован интерпретатор Python3.11.

### Последовательность установки
Для установки используемых библиотек нужных версий выполните команду в рабочей папке проекта:

pip install -r requirements.txt.

## Описание работы
Микросервис имеет API json интерфейс и html интерфейс. Взаимодействие между 
пользователем и элементами микросервиса описан следующей диаграммой:

![img.png](dataflow-Wildfire_monitoring_microservice_API.png)