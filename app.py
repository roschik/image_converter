from flask import Flask, render_template, request, redirect, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os
import io
import base64
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.config['RECAPTCHA_SITE_KEY'] = '6LcqkYgrAAAAAK6MIYHkrPWGsqWm9MjXKX3XMeFo'
app.config['RECAPTCHA_SECRET_KEY'] = '6LcqkYgrAAAAACzxxmSDJDXhIUUveuqQl8hHT8If'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def verify_recaptcha(token):
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
            'secret': app.config['RECAPTCHA_SECRET_KEY'],
            'response': token
        }
    )
    return response.json().get('success', False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def process_image(image_path):
    img = Image.open(image_path)
    img_array = np.array(img)

    # Разбиение на 4 части
    h, w = img_array.shape[0], img_array.shape[1]
    h = h - 1 if h % 2 != 0 else h
    w = w - 1 if w % 2 != 0 else w
    img_array = img_array[:h, :w]
    parts = [
        img_array[:h // 2, :w // 2],  # NW
        img_array[:h // 2, w // 2:],  # NE
        img_array[h // 2:, w // 2:],  # SE
        img_array[h // 2:, :w // 2]  # SW
    ]

    # Ротация по часовой стрелке
    rotated = np.vstack([
        np.hstack([parts[3], parts[0]]),
        np.hstack([parts[2], parts[1]])
    ])

    # Создание графика
    plt.figure(figsize=(8, 4))
    if len(img_array.shape) == 3:
        colors = ('r', 'g', 'b')
        for i, color in enumerate(colors):
            hist = np.histogram(img_array[:, :, i].ravel(), bins=256, range=(0, 256))
            plt.plot(hist[1][:-1], hist[0], color=color, label=color.upper())
        plt.legend()
    else:
        hist = np.histogram(img_array.ravel(), bins=256, range=(0, 256))
        plt.plot(hist[1][:-1], hist[0], color='black')

    plt.title('Color Distribution')
    plt.grid(True, alpha=0.3)

    # Конвертация графика в base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plot_url = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    return Image.fromarray(rotated), plot_url


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Проверка reCAPTCHA
        captcha_token = request.form.get('g-recaptcha-response')

        # Проверяем, был ли передан токен
        if not captcha_token:
            return "Ошибка: токен reCAPTCHA не получен", 400

        # Проверяем валидность токена
        if not verify_recaptcha(captcha_token):
            return "Пожалуйста, подтвердите, что вы не робот", 400

        # Обработка файла
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            rotated_img, plot_url = process_image(filepath)
            result_path = os.path.join(app.config['UPLOAD_FOLDER'], 'rotated_' + filename)
            rotated_img.save(result_path)

            return render_template('result.html',
                                   original=filename,
                                   result='rotated_' + filename,
                                   plot_url=plot_url)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)