import streamlit as st
import easyocr
import cv2
import numpy as np
import re
from PIL import Image

# Настройки страницы
st.set_page_config(page_title="Карта месторождений", layout="wide")

# Инициализация EasyOCR
reader = easyocr.Reader(['en'])

st.title("Карта месторождений")

# Шаг 1: Загрузка изображения пользователем
uploaded_file = st.file_uploader("Загрузите изображение карты (формат PNG или JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Прочитать загруженное изображение
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # Показать загруженное изображение
    st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), caption="Загруженное изображение карты", use_column_width=True)

    # Параметры скользящего окна
    window_size = 300
    step_size = 200
    height, width, _ = image.shape
    all_results = []

    # Шаг 2: Сканирование изображения с помощью EasyOCR
    for y in range(0, height - window_size, step_size):
        for x in range(0, width - window_size, step_size):
            section = image[y:y + window_size, x:x + window_size].copy()
            results = reader.readtext(section)
            for (bbox, text, prob) in results:
                global_bbox = [
                    (bbox[0][0] + x, bbox[0][1] + y),
                    (bbox[1][0] + x, bbox[1][1] + y),
                    (bbox[2][0] + x, bbox[2][1] + y),
                    (bbox[3][0] + x, bbox[3][1] + y)
                ]
                all_results.append((global_bbox, text, prob))

    # Шаг 3: Ввод названия месторождения
    target_name = st.text_input("Введите название месторождения (например, 'hf026'):")

    # Кнопка "Найти"
    if st.button("Найти"):
        found = False
        annotated_image = image.copy()

        for (bbox, text, prob) in all_results:
            if re.fullmatch(rf'\b{target_name}\b', text.lower()):
                found = True
                top_left = (int(bbox[0][0]), int(bbox[0][1]))
                bottom_right = (int(bbox[2][0]), int(bbox[2][1]))
                arrow_start = (top_left[0] - 70, top_left[1] - 120)  # Начало стрелки
                arrow_end = (top_left[0], top_left[1])  # Кончик стрелки на краю выделенной области

                # Нарисовать прямоугольник и большую стрелку
                cv2.rectangle(annotated_image, top_left, bottom_right, (0, 255, 0), 2)
                cv2.arrowedLine(annotated_image, arrow_start, arrow_end, (0, 0, 255), 6, tipLength=0.35)
                cv2.putText(annotated_image, text, (top_left[0], top_left[1] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if not found:
            st.markdown("<h2 style='color: red; text-align: center;'>Месторождение не найдено!</h2>", unsafe_allow_html=True)
        else:
            st.write(f"Месторождение '{target_name}' выделено на изображении.")

        # Показать обновлённое изображение с выделенной областью и стрелкой
        st.image(
            cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB),
            caption="Обновлённое изображение карты",
            use_column_width=True,
            output_format="PNG"
        )