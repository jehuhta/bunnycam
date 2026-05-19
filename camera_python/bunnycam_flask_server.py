from flask import Flask, request
from datetime import datetime
import shutil
import os, time
import yolo

app = Flask(__name__)

IR_DIR = "/media/jessurpi/ESD-USB/Bunnycam"
os.makedirs(IR_DIR, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload():

    img_bytes = request.data
    if not img_bytes:
        return "No data", 400

    img_type = request.args.get("type", "ir")
    device_id = request.args.get("device", "unknown")

    timestamp = int(time.time() * 1000)
    dt = datetime.fromtimestamp(timestamp / 1000)
    dt_str = dt.strftime("date_%d-%m-%y_hours_%H.%M.%S")

    path = os.path.join(IR_DIR, f"device_{device_id}_{dt_str}.jpg")

    

    with open(path, "wb") as f:
        f.write(img_bytes)

    print(f"Saved: {path} ({len(img_bytes)} bytes)")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)