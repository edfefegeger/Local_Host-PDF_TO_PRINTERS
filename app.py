import traceback
from flask import Flask, render_template, request
import os
import win32print
import requests
import hashlib
import urllib.parse
import threading
import time
from PyPDF2 import PdfReader
import pywintypes
import win32timezone

app = Flask(__name__)
print_complete_event = threading.Event()

def monitor_print_jobs(hPrinter, hJob):
    """
    Мониторит статус печатного задания и дожидается его завершения.
    """
    while True:
        try:
            # Получаем список заданий для принтера
            jobs = win32print.EnumJobs(hPrinter, 0, -1, 2)
        except pywintypes.error as e:
            # Если произошла ошибка, завершаем мониторинг
            break

        # Поиск задания с соответствующим дескриптором
        current_job = next((job for job in jobs if job['JobId'] == hJob), None)

        if current_job is not None:
            # Логируем статус задания
            print(f"Статус задания {hJob}: {current_job['Status']}")

            # Добавьте дополнительные логи по необходимости

            # Проверяем статус задания
            if current_job['Status'] == win32print.JOB_STATUS_COMPLETE:
                print("Печать завершена успешно")
                print_complete_event.set()
                break
            elif current_job['Status'] == win32print.JOB_STATUS_ERROR:
                print("Ошибка при печати")
                break
            elif current_job['Status'] == win32print.JOB_STATUS_DELETED:
                print("Задание удалено")
                break
            elif current_job['Status'] == win32print.PRINTER_STATUS_PRINTING:
                print("Принтер выполняет печать")

        # Пауза перед следующей проверкой статуса
        time.sleep(1)

        # Пауза перед следующей проверкой статуса
        time.sleep(1)


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

        # Завершаем печать
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)

        # Запускаем мониторинг печатного задания в отдельном потоке
        monitor_thread = threading.Thread(target=monitor_print_jobs, args=(hPrinter, hJob))
        monitor_thread.start()

        # Если код дошел до этого момента, считаем печать успешной
        success = True

    except Exception as e:
        print(f"Ошибка при печати: {e}")
        traceback.print_exc()
        print_complete_event.set()

    # Удаляем временный файл
    os.remove(unique_filename)

    # Возвращаем HTML-страницу с обновленным содержимым div и информацией о формате бумаги
    return render_template('index.html', result_message="Печать начата", paper_size=paper_size)

if __name__ == '__main__':
    
    # Запускаем Flask-приложение в отдельном потоке
    app_thread = threading.Thread(target=app.run, kwargs={'debug': True, 'use_reloader': False, 'threaded': True})
    app_thread.start()

    # Ждем, пока печать не завершится (или произошла бы ошибка)
    print_complete_event.wait()

    # Закрываем Flask-приложение
    app_thread.join()