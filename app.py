from flask import Flask, render_template, request, jsonify
import os
import win32print
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/print', methods=['GET'])
@app.route('/print', methods=['GET'])
@app.route('/print', methods=['GET'])
def print_file():
    file_url = request.args.get('file_url')
    paper_size = request.args.get('paper_size')
    printer_name = request.args.get('printer_name')

    # Скачиваем файл
    response = requests.get(file_url)
    with open('temp_file.pdf', 'wb') as f:
        f.write(response.content)

    # Устанавливаем принтер по умолчанию
    win32print.SetDefaultPrinter(printer_name)

    # Получаем информацию о принтере по умолчанию
    default_printer = win32print.GetDefaultPrinter()
    # Получаем информацию о принтере
    printer_info = win32print.GetPrinter(win32print.OpenPrinter(default_printer))

    # Задаем параметры печати
    print_data = {
        'Title': 'Print Job',
        'PrintToFile': False,
        'PaperSize': getattr(win32print, paper_size),
        'PrintQuality': getattr(win32print, 'DPI_HIGH'),
    }

    # Печатаем файл
    win32print.StartDocPrinter(printer_info['hPrinter'], 1, (os.path.basename('temp_file.pdf'), None, 'RAW'))
    win32print.WritePrinter(printer_info['hPrinter'], response.content)
    win32print.EndDocPrinter(printer_info['hPrinter'])
    win32print.ClosePrinter(printer_info['hPrinter'])

    # Удаляем временный файл
    os.remove('temp_file.pdf')

    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True)