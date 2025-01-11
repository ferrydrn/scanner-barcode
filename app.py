from flask import Flask, render_template, request, send_file
import cv2
from pyzbar.pyzbar import decode
import csv
import os
from datetime import datetime

app = Flask(__name__)

# Nama file CSV
csv_file = "scanned_barcodes.csv"

# Inisialisasi file CSV
if not os.path.exists(csv_file):
    with open(csv_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Barcode", "Scan Date"])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan_barcode():
    video_capture = cv2.VideoCapture(0)
    scanned_data = []
    
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        # Deteksi barcode
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            barcode_data = obj.data.decode("utf-8")
            if barcode_data not in scanned_data:
                scanned_data.append(barcode_data)
                scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(csv_file, mode="a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([barcode_data, scan_date])
                print(f"Barcode Detected: {barcode_data} at {scan_date}")
        
        cv2.imshow("Barcode Scanner", frame)
        key = cv2.waitKey(1) & 0xFF
        
        # Tekan 'q' untuk keluar dari scanner
        if key == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return "Scanning complete. Data saved to CSV."

@app.route('/download', methods=['GET'])
def download_csv():
    return send_file(csv_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
