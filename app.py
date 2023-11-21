from flask import Flask, render_template, request, jsonify
import os
import win32print
import requests
import traceback  # Добавленный импорт
import hashlib
import urllib.parse

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/print', methods=['GET'])
def print_file():
    file_url = request.args.get('file_url')
    paper_size = request.args.get('paper_size')
    printer_name = request.args.get('printer_name')

    # Sanitize URL and create a unique name for the temporary file based on URL and paper size
    sanitized_url = hashlib.sha256(file_url.encode()).hexdigest()
    sanitized_url = urllib.parse.quote_plus(sanitized_url)  # Replace problematic characters with URL-safe characters
    unique_filename = f'temp_file_{sanitized_url}_size_{paper_size}.pdf'

    # Download the file
    response = requests.get(file_url)
    with open(unique_filename, 'wb') as f:
        f.write(response.content)

    success = False

    try:
        # Open the specified printer
        hPrinter = win32print.OpenPrinter(printer_name)
        
        # Get the default printer settings
        default_printer_settings = win32print.GetPrinter(hPrinter, 2)['pDevMode']

        # Set the paper size
        default_printer_settings.PaperSize = getattr(win32print, 'DMPAPER_' + paper_size, default_printer_settings.PaperSize)

        # Set up print data
        print_data = {
            'Title': 'Print Job',
            'PrintToFile': False,
            'pDevMode': default_printer_settings,
        }

        # Start printing
        hJob = win32print.StartDocPrinter(hPrinter, 1, (unique_filename, None, 'RAW'))
        win32print.StartPagePrinter(hPrinter)

        # Read the content of the PDF file and write it to the printer
        with open(unique_filename, 'rb') as pdf_file:
            win32print.WritePrinter(hPrinter, pdf_file.read())

        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)

        # If code reaches here, consider printing successful
        success = True

    except Exception as e:
        print(f"Error printing: {e}")
        traceback.print_exc()

    finally:
        # Close the printer handle
        win32print.ClosePrinter(hPrinter)

    # Remove the temporary file
    os.remove(unique_filename)

    # Check if printing was successful
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'failure'})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, threaded=True)
