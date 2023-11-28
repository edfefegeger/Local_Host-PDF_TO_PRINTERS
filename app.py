import hashlib
import os
import requests
import subprocess
from flask import Flask, render_template, request
from flask import jsonify
import win32print

app = Flask(__name__)

def set_sumatra_paper_size(settings_path, paper_size):
    with open(settings_path, 'a') as settings_file:
        settings_file.write(f'CustomPageSize = {paper_size}\n')

def print_pdf(file_path, printer_name):
    sumatra_path = r'SumatraPDF\SumatraPDF.exe'
    subprocess.run([sumatra_path, '-print-to', printer_name, file_path])

@app.route('/get_printers')
def get_printers():
    printers = [printer[2] for printer in win32print.EnumPrinters(2)]
    return jsonify({'printers': printers})
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/print', methods=['GET'])
def print_file():
    file_url = request.args.get('file_url')
    paper_size = request.args.get('paper_size')
    printer_name = request.args.get('printer_name')
    page_orientation = request.args.get('page_orientation', 'portrait')  # По умолчанию 'portrait', если параметр не передан

    sanitized_url = hashlib.sha256(file_url.encode()).hexdigest()
    sanitized_url = sanitized_url[:10]
    unique_filename = f'temp_file_{sanitized_url}_size_{paper_size}_orientation_{page_orientation}.pdf'

    response = requests.get(file_url)
    with open(unique_filename, 'wb') as f:
        f.write(response.content)

    # Указать путь к файлу SumatraPDF-settings.txt
    sumatra_settings_path = os.path.join(os.path.dirname('SumatraPDF\SumatraPDF.exe'), 'SumatraPDF-settings.txt')

    success = False

    try:
        # Добавить размер бумаги и ориентацию к параметрам
        set_sumatra_paper_size(sumatra_settings_path, f'{paper_size} {page_orientation}')
        print_pdf(unique_filename, printer_name)
        success = True
    except Exception as e:
        print(f"Error while printing: {e}")
    finally:
        os.remove(unique_filename)

    return render_template('index.html', result_message="Printing initiated", paper_size=paper_size, success=success)


if __name__ == '__main__':
    app.run(debug=True)
