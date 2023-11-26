import traceback
from flask import Flask, render_template, request
import os
import win32printing
import requests
import hashlib
import urllib.parse
import tempfile
import fitz  # PyMuPDF
import win32timezone

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
        # Open the printer
        with win32printing.Printer(printer_name) as printer:
            # Start a print job
            printer.text(f"Printing file: {file_url}")

            # Send the PDF content to the printer
            with open(unique_filename, 'rb') as pdf_file:
                # Using PyMuPDF to read the PDF content
                pdf_document = fitz.open(pdf_file)
                
                for page_number in range(pdf_document.page_count):
                    page = pdf_document.load_page(page_number)
                    page_text = page.get_text()
                    
                    # Send the text to the printer
                    printer.text(page_text)

        success = True

    except Exception as e:
        print(f"Error while printing: {e}")
        traceback.print_exc()

    return render_template('index.html', result_message="Printing initiated", paper_size=paper_size)

if __name__ == '__main__':
    app.run(debug=True)
