import hashlib
import os
import requests
import subprocess
from flask import Flask, render_template, request
from flask import jsonify
import win32print

app = Flask(__name__)

def print_pdf(file_path, printer_name, paper_size, page_orientation):
    sumatra_path = r'SumatraPDF\SumatraPDF.exe'
    
    # Параметры командной строки для управления печатью в SumatraPDF
    command_line = [
        sumatra_path,
        '-print-to', printer_name,
        '-print-settings', f'paper={paper_size},{page_orientation}',
        file_path
    ]

    subprocess.run(command_line)

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
    page_orientation = request.args.get('page_orientation')  # По умолчанию 'portrait', если параметр не передан

    sanitized_url = hashlib.sha256(file_url.encode()).hexdigest()
    sanitized_url = sanitized_url[:10]
    unique_filename = f'temp_file_{sanitized_url}_size_{paper_size}_orientation_{page_orientation}.pdf'

    response = requests.get(file_url)
    with open(unique_filename, 'wb') as f:
        f.write(response.content)

    success = False

    try:
        print_pdf(unique_filename, printer_name, paper_size, page_orientation)
        success = True
    except Exception as e:
        print(f"Error while printing: {e}")
    finally:
        os.remove(unique_filename)

    return render_template('index.html', result_message="Printing initiated", paper_size=paper_size, success=success)

if __name__ == '__main__':
    app.run(debug=True)