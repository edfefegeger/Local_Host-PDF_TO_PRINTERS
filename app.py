from flask import Flask, render_template, request, jsonify
import os
import win32print
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/print', methods=['GET'])
def print_file():
    file_url = request.args.get('file_url')
    paper_size = request.args.get('paper_size')
    printer_name = request.args.get('printer_name')

    # Download the file
    response = requests.get(file_url)
    with open('temp_file.pdf', 'wb') as f:
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
        hJob = win32print.StartDocPrinter(hPrinter, 1, (file_url, None, 'RAW'))
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, response.content)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)

        # If code reaches here, consider printing successful
        success = True

    finally:
        # Close the printer handle
        win32print.ClosePrinter(hPrinter)

    # Remove the temporary file
    os.remove('temp_file.pdf')

    # Check if printing was successful
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'failure'})

if __name__ == '__main__':
    app.run(debug=True)
