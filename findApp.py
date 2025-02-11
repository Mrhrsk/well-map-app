import cv2
import numpy as np
import streamlit as st
import easyocr
from PIL import ImageEnhance, Image

st.set_page_config(page_title="Карта месторождений", layout="wide")
st.title("Карта месторождений")

# Инициализация EasyOCR с английским языком
reader = easyocr.Reader(['en'])

# Загрузка изображения пользователем
uploaded_file = st.file_uploader("Загрузите изображение карты (формат PNG или JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Преобразуем загруженное изображение в массив numpy
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # Функция улучшения изображения: увеличение контрастности и резкости
    def enhance_image(img):
        # Преобразуем изображение в LAB и разделяем каналы
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        # Применяем CLAHE к каналу яркости
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        merged = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        # Применяем фильтр резкости для улучшения качества
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        return sharpened

    # Применяем улучшение изображения
    enhanced_image = enhance_image(image)
    st.image(cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2RGB), 
             caption="Улучшенное изображение", use_column_width=True)

    # Выполняем OCR на полном улучшенном изображении с разрешённым набором символов
    results_full = reader.readtext(enhanced_image,
                                   allowlist='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    all_results = []
    all_results.extend(results_full)
    
    # Метод скользящего окна: размер окна 600, шаг 300
    window_size = 600
    step_size = 300
    height, width, _ = enhanced_image.shape

    for y in range(0, height - window_size + 1, step_size):
        for x in range(0, width - window_size + 1, step_size):
            section = enhanced_image[y:y + window_size, x:x + window_size]
            results = reader.readtext(section,
                                      allowlist='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
            for (bbox, text, prob) in results:
                # Преобразуем координаты bbox к координатам исходного изображения
                global_bbox = [
                    (bbox[0][0] + x, bbox[0][1] + y),
                    (bbox[1][0] + x, bbox[1][1] + y),
                    (bbox[2][0] + x, bbox[2][1] + y),
                    (bbox[3][0] + x, bbox[3][1] + y)
                ]
                all_results.append((global_bbox, text, prob))

    # Ввод названия месторождения для поиска
    target_name = st.text_input("Введите название месторождения для поиска:")

    if st.button("Найти"):
        found = False
        # Используем улучшенное изображение для аннотации (выше качество)
        annotated_image = enhanced_image.copy()
        target_name_clean = target_name.strip().lower()

        for (bbox, text, prob) in all_results:
            detected_text = text.strip().lower()
            if target_name_clean in detected_text:
                found = True
                top_left = (int(bbox[0][0]), int(bbox[0][1]))
                bottom_right = (int(bbox[2][0]), int(bbox[2][1]))
                arrow_start = (top_left[0] - 70, top_left[1] - 120)
                arrow_end = (top_left[0], top_left[1])

                # Рисуем прямоугольник, стрелку и подписываем найденный текст
                cv2.rectangle(annotated_image, top_left, bottom_right, (0, 255, 0), 2)
                cv2.arrowedLine(annotated_image, arrow_start, arrow_end, (0, 0, 255), 6, tipLength=0.35)
                cv2.putText(annotated_image, text, (top_left[0], top_left[1] - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if not found:
            st.markdown("<h2 style='color: red; text-align: center;'>Месторождение не найдено!</h2>",
                        unsafe_allow_html=True)
        else:
            st.write(f"Месторождение '{target_name}' выделено на изображении.")
            st.image(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB),
                     caption="Обновлённое изображение карты", use_column_width=True)
