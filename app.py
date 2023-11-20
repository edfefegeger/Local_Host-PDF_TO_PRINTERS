from flask import Flask, render_template, request, jsonify
import os
import win32print
import win32con
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

    try:
        # Open the specified printer
        hPrinter = win32print.OpenPrinter(printer_name)
        
        # Get the default printer settings
        default_printer_settings = win32print.GetPrinter(hPrinter, 2)['pDevMode']

        # Print some debugging information
        print("Printer Name:", printer_name)
        print("Supported Paper Sizes:", default_printer_settings.PaperSize)
        
        # Set the paper size
        default_printer_settings.PaperSize = getattr(win32print, 'DMPAPER_' + paper_size, default_printer_settings.PaperSize)

        # Print additional debugging information
        print("Selected Paper Size:", default_printer_settings.PaperSize)

        # Set up print data
        print_data = {
            'Title': 'Print Job',
            'PrintToFile': False,
            'pDevMode': default_printer_settings,
        }

        # Print additional debugging information
        print("Print Data:", print_data)

        # Start printing
        hJob = win32print.StartDocPrinter(hPrinter, 1, ('temp_file.pdf', None, 'RAW'))
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, response.content)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)

    finally:
        # Close the printer handle
        win32print.ClosePrinter(hPrinter)

    # Remove the temporary file
    os.remove('temp_file.pdf')

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
