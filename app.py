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

from flask import Flask, render_template, request
import win32printing

app = Flask(__name__)

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
        with win32printing.Printer() as printer:
            printer.text(f"Printing file: {file_url}")

        success = True

    except win32printing.error as e:
        print(f"Error while printing: {e}")
        traceback.print_exc()

    return render_template('index.html', result_message="Printing initiated", paper_size=paper_size)

if __name__ == '__main__':
    app.run(debug=True)
