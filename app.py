from flask import Flask, render_template, Response, jsonify
import cv2
import threading
from pyzbar.pyzbar import decode
from datetime import datetime
import csv

app = Flask(__name__)
camera = None
lock = threading.Lock()

# File CSV untuk mencatat hasil pemindaian
csv_file = "scanned_barcodes.csv"
current_barcode = {"code": ""}

# Fungsi untuk memulai kamera
def start_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)

# Fungsi untuk menghentikan kamera
def stop_camera():
    global camera
    if camera and camera.isOpened():
        camera.release()

# Fungsi untuk mengakses frame kamera
def generate_frames():
    global camera
    while True:
        with lock:
            if camera is None or not camera.isOpened():
                break
            success, frame = camera.read()
        if not success:
            break
        else:
            # Encode frame sebagai JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Fungsi untuk memindai barcode
def scan_barcode_from_frame(frame):
    decoded_objects = decode(frame)
    for obj in decoded_objects:
        barcode_data = obj.data.decode("utf-8")
        if barcode_data != current_barcode["code"]:
            current_barcode["code"] = barcode_data
            scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Simpan hasil ke CSV
            with open(csv_file, mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([barcode_data, scan_date])

# Rute untuk memulai kamera
@app.route('/start', methods=['POST'])
def start():
    start_camera()
    return jsonify({"status": "Camera started"})

# Rute untuk menghentikan kamera
@app.route('/stop', methods=['POST'])
def stop():
    stop_camera()
    return jsonify({"status": "Camera stopped"})

# Rute untuk stream video
@app.route('/video_feed')
def video_feed():
    start_camera()
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Rute untuk mendapatkan barcode terbaru
@app.route('/get_barcode')
def get_barcode():
    with lock:
        if camera and camera.isOpened():
            ret, frame = camera.read()
            if ret:
                scan_barcode_from_frame(frame)
    return jsonify({"barcode": current_barcode["code"]})

# Rute utama
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
