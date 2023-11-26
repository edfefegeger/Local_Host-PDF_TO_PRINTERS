import hashlib
import os
import requests
import subprocess
from flask import Flask, render_template, request

app = Flask(__name__)

def print_pdf(file_path, printer_name):
    sumatra_path = r'SumatraPDF\SumatraPDF.exe'
    subprocess.run([sumatra_path, '-print-to', printer_name, file_path])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/print', methods=['GET'])
def print_file():
    file_url = request.args.get('file_url')
    paper_size = request.args.get('paper_size')
    printer_name = request.args.get('printer_name')

    sanitized_url = hashlib.sha256(file_url.encode()).hexdigest()
    sanitized_url = sanitized_url[:10]
    unique_filename = f'temp_file_{sanitized_url}_size_{paper_size}.pdf'

    response = requests.get(file_url)
    with open(unique_filename, 'wb') as f:
        f.write(response.content)

    success = False

    try:
        print_pdf(unique_filename, printer_name)
        success = True
    except Exception as e:
        print(f"Error while printing: {e}")
    finally:
        # Удаление временного файла после завершения
        os.remove(unique_filename)

    return render_template('index.html', result_message="Printing initiated", paper_size=paper_size, success=success)

if __name__ == '__main__':
    app.run(debug=True)
