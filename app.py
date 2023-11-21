from flask import Flask, render_template, request, jsonify
import os
import win32print
import requests
import traceback  # Добавленный импорт
import hashlib
import urllib.parse
import webbrowser

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/print', methods=['GET'])
def print_file():
    # Получаем URL, размер бумаги и имя принтера из параметров запроса
    file_url = request.args.get('file_url')
    paper_size = request.args.get('paper_size')
    printer_name = request.args.get('printer_name')

    # Очищаем URL и создаем уникальное имя временного файла на основе URL и размера бумаги
    sanitized_url = hashlib.sha256(file_url.encode()).hexdigest()
    sanitized_url = urllib.parse.quote_plus(sanitized_url)  # Заменяем проблемные символы на безопасные для URL
    unique_filename = f'temp_file_{sanitized_url}_size_{paper_size}.pdf'

    # Загружаем файл
    response = requests.get(file_url)
    with open(unique_filename, 'wb') as f:
        f.write(response.content)

    success = False

    try:
        # Открываем указанный принтер
        hPrinter = win32print.OpenPrinter(printer_name)
        
        # Получаем параметры по умолчанию принтера
        default_printer_settings = win32print.GetPrinter(hPrinter, 2)['pDevMode']

        # Устанавливаем размер бумаги
        default_printer_settings.PaperSize = getattr(win32print, paper_size, default_printer_settings.PaperSize)

        # Подготавливаем данные для печати
        print_data = {
            'Title': 'Print Job',
            'PrintToFile': False,
            'pDevMode': default_printer_settings,
        }

        # Начинаем печать
        hJob = win32print.StartDocPrinter(hPrinter, 1, (unique_filename, None, 'RAW'))
        win32print.StartPagePrinter(hPrinter)

        # Читаем содержимое файла PDF и записываем его в принтер
        with open(unique_filename, 'rb') as pdf_file:
            win32print.WritePrinter(hPrinter, pdf_file.read())

        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)

        # Если код дошел до этого момента, считаем печать успешной
        success = True

    except Exception as e:
        print(f"Ошибка при печати: {e}")
        traceback.print_exc()

    finally:
        # Закрываем дескриптор принтера
        win32print.ClosePrinter(hPrinter)

    # Удаляем временный файл
    os.remove(unique_filename)

    # Проверяем успешность печати
    if success:
        result_message = 'Успешная печать'
    else:
        result_message = 'Ошибка при печати'

    # Возвращаем HTML-страницу с обновленным содержимым div и информацией о формате бумаги
    return render_template('index.html', result_message=result_message, paper_size=paper_size)

if __name__ == '__main__':
    # Открываем браузер с локальным хостом после запуска приложения
    webbrowser.open('http://127.0.0.1:5000/')

    # Запускаем Flask-приложение
    app.run(debug=True, use_reloader=False, threaded=True)
