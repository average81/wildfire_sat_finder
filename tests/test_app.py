
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
import numpy as np
import PIL.Image

# Импортируем классы из основного модуля
# для import NASAAPI, SentinelHubAPI, FileHandler, ImageProcessor, convert_image

class TestNASAAPI(unittest.TestCase):
    """Тестирование класса NASAAPI."""

    @patch('requests.get')
    def test_fetch_image_success(self, mock_get):
        """Тест успешного получения изображения."""
        # Настраиваем поддельный ответ
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b'fake_image_data'
        mock_get.return_value = mock_response

        api = NASAAPI(api_key="dummy_key")
        with patch('PIL.Image.open', return_value=PIL.Image.new('RGB', (100, 100))):
            image = api.fetch_image(39.2106, -121.6701, '2019-01-02')
            self.assertIsInstance(image, PIL.Image.Image)

    @patch('requests.get')
    def test_fetch_image_http_error(self, mock_get):
        """Тест обработки HTTP ошибки."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        api = NASAAPI(api_key="dummy_key")
        with self.assertRaises(requests.HTTPError):
            api.fetch_image(39.2106, -121.6701, '2019-01-02')

    @patch('requests.get')
    def test_fetch_image_invalid_content(self, mock_get):
        """Тест обработки недопустимого содержимого изображения."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b'not_an_image'
        mock_get.return_value = mock_response

        api = NASAAPI(api_key="dummy_key")
        with patch('PIL.Image.open', side_effect=IOError("Cannot open image")):
            with self.assertRaises(ValueError):
                api.fetch_image(39.2106, -121.6701, '2019-01-02')


class TestSentinelHubAPI(unittest.TestCase):
    """Тестирование класса SentinelHubAPI."""

    @patch('sentinelhub.SentinelHubRequest.get_data')
    def test_fetch_image_success(self, mock_get_data):
        """Тест успешного получения изображения."""
        mock_get_data.return_value = [np.zeros((700, 700, 3), dtype=np.uint8)]

        api = SentinelHubAPI(client_id="dummy_id", client_secret="dummy_secret")
        image = api.fetch_image(39.2106, -121.6701, '2019-01-02', '2019-01-03', 0.5, 0.4)
        self.assertIsInstance(image, PIL.Image.Image)

    @patch('sentinelhub.SentinelHubRequest.get_data')
    def test_fetch_image_no_data(self, mock_get_data):
        """Тест обработки случая, когда данные не получены."""
        mock_get_data.return_value = []

        api = SentinelHubAPI(client_id="dummy_id", client_secret="dummy_secret")
        with self.assertRaises(ValueError):
            api.fetch_image(39.2106, -121.6701, '2019-01-02', '2019-01-03', 0.5, 0.4)

    def test_init_invalid_credentials(self):
        """Тест инициализации с недопустимыми учетными данными."""
        with self.assertRaises(ValueError):
            SentinelHubAPI(client_id="", client_secret="")

class TestFileHandler(unittest.TestCase):
    """Тестирование класса FileHandler."""

    def test_upload_file_success(self):
        """Тест успешной обработки загруженного файла."""
        handler = FileHandler()
        # Создаем простое изображение в памяти
        img = PIL.Image.new('RGB', (100, 100), color='red')
        buf = BytesIO()
        img.save(buf, format='JPEG')
        byte_data = buf.getvalue()

        image_array = handler.upload_file(byte_data)
        self.assertIsInstance(image_array, np.ndarray)
        self.assertEqual(image_array.shape, (100, 100, 3))

    def test_upload_file_invalid_data(self):
        """Тест обработки недопустимых данных файла."""
        handler = FileHandler()
        byte_data = b'not_an_image'

        with self.assertRaises(ValueError):
            handler.upload_file(byte_data)


class TestImageProcessor(unittest.TestCase):
    """Тестирование класса ImageProcessor."""

    @patch('tempfile.NamedTemporaryFile')
    @patch('cv2.imwrite')
    @patch('inference_sdk.InferenceHTTPClient.infer')
    def test_run_inference_success(self, mock_infer, mock_imwrite, mock_tempfile):
        """Тест успешного запуска инференса."""
        mock_infer.return_value = {
            "predictions": [
                {"class": "fire", "confidence": 0.95, "x": 0.5, "y": 0.5, "width": 0.1, "height": 0.1}
            ],
            "time": 123,
        }
        mock_temp = MagicMock()
        mock_tempfile.return_value.__enter__.return_value = mock_temp

        model = InferenceHTTPClient(api_url="", api_key="")
        processor = ImageProcessor(model)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = processor.run_inference(image)

        self.assertIn("predictions", result)
        self.assertEqual(result["time"], 123)
        self.assertEqual(result["width"], 100)
        self.assertEqual(result["height"], 100)


class TestConvertImage(unittest.TestCase):
    """Тестирование функции convert_image."""

    def test_convert_image_pil(self):
        """Тест конвертации PIL.Image.Image в numpy.ndarray."""
        pil_image = PIL.Image.new('RGB', (100, 100), color='blue')
        image_array = convert_image(pil_image)
        self.assertIsInstance(image_array, np.ndarray)
        self.assertEqual(image_array.shape, (100, 100, 3))
        # Проверяем порядок цветов BGR
        self.assertTrue((image_array[:, :, 0] == 255).all())  # Blue channel

    def test_convert_image_bytes(self):
        """Тест конвертации байт в numpy.ndarray."""
        pil_image = PIL.Image.new('RGB', (100, 100), color='green')
        buf = BytesIO()
        pil_image.save(buf, format='PNG')
        byte_data = buf.getvalue()
        image_array = convert_image(byte_data)
        self.assertIsInstance(image_array, np.ndarray)
        self.assertEqual(image_array.shape, (100, 100, 3))
        # Проверяем порядок цветов BGR
        self.assertTrue((image_array[:, :, 1] == 255).all())  # Green channel

    def test_convert_image_numpy(self):
        """Тест передачи numpy.ndarray без изменений."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image_array = convert_image(image)
        self.assertIs(image_array, image)

    def test_convert_image_invalid_type(self):
        """Тест обработки недопустимого типа изображения."""
        with self.assertRaises(ValueError):
            convert_image("not_an_image")

    def test_convert_image_invalid_format(self):
        """Тест обработки изображения с неверным форматом."""
        pil_image = PIL.Image.new('L', (100, 100))  # Grayscale image
        with self.assertRaises(ValueError):
            convert_image(pil_image)


if __name__ == '__main__':
    unittest.main()