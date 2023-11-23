import traceback
from flask import Flask, render_template, request
import os
import win32print
import requests
import hashlib
import urllib.parse
import threading
import time
from PyPDF2 import PdfReader, PdfWriter
import pywintypes
import win32timezone

app = Flask(__name__)
print_complete_event = threading.Event()

def monitor_print_jobs(hPrinter, hJob):
    while True:
        try:
            jobs = win32print.EnumJobs(hPrinter, 0, -1, 2)
        except pywintypes.error as e:
            break

        current_job = next((job for job in jobs if job['JobId'] == hJob), None)

        if current_job is not None:
            print(f"Информация о задании {hJob}: {current_job}")

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

        time.sleep(1)

    win32print.ClosePrinter(hPrinter)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/print', methods=['GET'])
def print_file():
    file_url = request.args.get('file_url')
    paper_size = request.args.get('paper_size')
    printer_name = request.args.get('printer_name')

    sanitized_url = hashlib.sha256(file_url.encode()).hexdigest()
    sanitized_url = urllib.parse.quote_plus(sanitized_url)
    unique_filename = f'temp_file_{sanitized_url}_size_{paper_size}.pdf'

    response = requests.get(file_url)
    with open(unique_filename, 'wb') as f:
        f.write(response.content)

    success = False

    try:
        hPrinter = win32print.OpenPrinter(printer_name)
        default_printer_settings = win32print.GetPrinter(hPrinter, 2)['pDevMode']
        default_printer_settings.PaperSize = getattr(win32print, paper_size, default_printer_settings.PaperSize)

        pdf_reader = PdfReader(unique_filename)
        pdf_writer = PdfWriter()

        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])

        new_unique_filename = f'processed_temp_file_{sanitized_url}_size_{paper_size}.pdf'
        with open(new_unique_filename, 'wb') as pdf_file:
            pdf_writer.write(pdf_file)

        hJob = win32print.StartDocPrinter(hPrinter, 1, (new_unique_filename, None, 'RAW'))
        win32print.StartPagePrinter(hPrinter)

        with open(new_unique_filename, 'rb') as pdf_file:
            win32print.WritePrinter(hPrinter, pdf_file.read())

        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)

        monitor_thread = threading.Thread(target=monitor_print_jobs, args=(hPrinter, hJob))
        monitor_thread.start()

        success = True

    except Exception as e:
        print(f"Ошибка при печати: {e}")
        traceback.print_exc()
        print_complete_event.set()

    return render_template('index.html', result_message="Печать начата", paper_size=paper_size)

if __name__ == '__main__':
    app.run(debug=True)
