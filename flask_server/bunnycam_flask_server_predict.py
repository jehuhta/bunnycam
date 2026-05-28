from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import time
import shutil
import os, time
from ultralytics import YOLO
import cv2
import numpy as np
import duckdb
import logging
import base64

# Constants
MODEL_VERSION = 6
NUM_CLASSES = 2
CLASS_NAMES = ["Aune","Dippi"]
DECAY = .15
THRESHOLD = 1.0
IR_DIR = "/media/jessurpi/ESD-USB/Bunnycam"
PRED_DIR = "/media/jessurpi/ESD-USB/Bunnycam_frame_predictions"

# Supress logging for each post.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

model = YOLO(r"/home/jessurpi/bunnycam/model6.pt")
app = Flask(__name__)
os.makedirs(IR_DIR, exist_ok=True)
os.makedirs(PRED_DIR, exist_ok=True)
con = duckdb.connect("/home/jessurpi/bunnycam/bunnycam.db")

# Creates a tables if they do not exist. These are required to log/run
# the flask server.
con.sql("""
CREATE TABLE IF NOT EXISTS rabbit_predict(
    id INTEGER PRIMARY KEY,
    Timestamp TIMESTAMP_S,
    Timestamp_str VARCHAR(50),
    Device VARCHAR(20),
    model INT,
    Aune_conf FLOAT,
    Dippi_conf FLOAT,
    Aune_score FLOAT,
    Dippi_score FLOAT,
    Dippi_detected BOOLEAN,
    Aune_detected BOOLEAN,
    Path VARCHAR(70),
    Path_Predict VARCHAR(70)
);
""")


# HTML Request which:
# 1. Saves images from the ESP32-S3.
# 2. Predicts them using yolo.
# 3. Parses results.
# 4. Retrieves metadata and other information such as timestamps.
# 5. Stores the information into the proper DUCKDB tables.
@app.route("/upload", methods=["POST"])
def upload():

    print("-------------------------------------")
    print("New frame detected, saving...")

    # -- RETRIEVAL -- 
    # Retrieve the picture from the ESP32 in bytes format
    img_bytes = request.data
    if not img_bytes:
        return "No data", 400
    
    # Retrieve the picture and the device name
    img_type = request.args.get("type", "ir")
    device_id = request.args.get("device", "unknown")

    # Get the datetime
    timestamp = int(time.time() * 1000)
    dt = datetime.fromtimestamp(timestamp / 1000)
    dt_str = dt.strftime("date_%d-%m-%y_hours_%H.%M.%S")


    # -- SAVING UNPREDICTED IMAGE -- 
    # Set the path and name to write the jpg into storage. 
    # The IR_DIR is the storage for the jpg files.
    path = os.path.join(IR_DIR, f"device_{device_id}_{dt_str}.jpg")
    with open(path, "wb") as f:
        f.write(img_bytes)
        print(f"      Frame saved: {path} ({len(img_bytes)} bytes)")
    

    # -- PREDICTION --
    print("Predicting...")

    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    # Predict frame.
    results = model.predict(frame, imgsz=(1600,1216), conf=.25, verbose=False)
    
    # Save the image of the results
    pred_dir_path = f"{PRED_DIR}/predicted_device_{device_id}_{dt_str}.jpg"
    results[0].save(filename=pred_dir_path)
    
    # Get highest confidence value per class.
    boxes = results[0].boxes
    if boxes:
        classes = boxes.cls.tolist()
        confs = boxes.conf.tolist()
        
        class_confs = {}
        for cls, conf in zip(classes, confs):
            class_name = model.names[int(cls)]
            if class_name not in class_confs or conf > class_confs[class_name]:
                class_confs[class_name] = conf
    else:
        class_confs = {0:0}
    
    print(f"      Frame predictions: {class_confs}")
    
    # -- CALCULATING PREDICTION SCORES --
    # Retrieve the last scores from the dataset.
    last_row = con.sql("""
        SELECT Aune_score, Dippi_score FROM rabbit_predict
        ORDER BY id DESC LIMIT 1 
    """).fetchone()
    
    # Adds the last row's scores to a list
    if last_row:
        prev_aune_score, prev_dippi_score = last_row
    else:
        prev_aune_score, prev_dippi_score = 0, 0
    print(f"      Previous scores: Aune: {prev_aune_score}, Dippi: {prev_dippi_score}")
     
    # True if score goes over threshold.
    aune_detected = prev_aune_score > THRESHOLD
    dippi_detected = prev_dippi_score > THRESHOLD

    # -- DUCKDB STORAGE --
    # Prep row to insert into DUCKDB.
    data = {
        "Timestamp": dt,
        "Timestamp_str": dt_str,
        "Device": device_id,
        "Model": MODEL_VERSION,
        "Aune_conf": class_confs.get("Aune", 0),
        "Dippi_conf": class_confs.get("Dippi", 0),
        "Aune_score": (prev_aune_score * (1 - DECAY)) + class_confs.get("Aune", 0),
        "Dippi_score": (prev_dippi_score * (1 - DECAY)) + class_confs.get("Dippi", 0),
        "Aune_detected": aune_detected,
        "Dippi_detected": dippi_detected,
        "Path": path,
        "Path_predict": pred_dir_path
    }
    
    # Insert as row into rabbit_predict DUCKDB table.
    con.sql(f"""
        INSERT INTO rabbit_predict (
            id,
            Timestamp,
            Timestamp_str,
            Device,
            Model,
            Aune_conf,
            Dippi_conf,
            Aune_score,
            Dippi_score,
            Aune_detected,
            Dippi_detected,
            Path,
            Path_predict
            )
        SELECT 
            COALESCE(MAX(id), 0) + 1,
            $Timestamp,
            $Timestamp_str,
            $Device,
            $Model, 
            $Aune_conf, 
            $Dippi_conf, 
            $Aune_score,
            $Dippi_score,
            $Aune_detected,
            $Dippi_detected,
            $Path,
            $Path_predict
        FROM rabbit_predict;
    """, params=data)
    print("      Stored into database.")

    return "OK", 200

# This HTML request returns the rabbit_predict DUCKDB table in json.
@app.route("/table_main", methods=["GET"])
def get_table_main():
    rows = con.execute("""
    SELECT 
        Timestamp_str,
        Device,
        Model, 
        Aune_conf, 
        Dippi_conf, 
        Aune_score,
        Dippi_score,
        Aune_detected,
        Dippi_detected
    FROM rabbit_predict 
    ORDER BY id DESC 
    LIMIT 20000
    """).fetchdf()

    return rows.to_json(orient="records"), 200, {"Content-Type": "application/json"}    

# HTML request pipeline which returns a list of basic information for the dashboard.
@app.route("/essentials", methods=["GET"])
def get_essentials():
    essential_stats = {}
    
    # Retrieve the current time.
    essential_stats["Time_now"] = datetime.now().strftime("%d-%m-%y %H:%M:%S")
    
    # Basic statistics for when Dippi and Aune were last seen.
    for class_name in CLASS_NAMES:
        last_detected = con.sql(f"""
        SELECT Timestamp_str
        FROM rabbit_predict
        WHERE {class_name}_detected
        ORDER BY Timestamp_str DESC
        LIMIT 1;
        """).fetchone()
        
        if last_detected:
            dt_last_detected = datetime.strptime(last_detected[0], "date_%d-%m-%y_hours_%H.%M.%S")
            essential_stats[f"{class_name}_last"] = dt_last_detected.strftime("%d.%m.%y   %H:%M:%S")
            time_since = datetime.now() - dt_last_detected

        else:
            essential_stats[f"{class_name}_last"] = "Nothing yet!"
            essential_stats[f"{class_name}_time_since"] = "N/A"
        
        total_seconds = int(time_since.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        essential_stats[f"{class_name}_time_since"] = f"{days}d {hours}h {minutes}m {seconds}s"
        essential_stats[f"{class_name}_time_since_minutes"] = round((total_seconds / 60), 0)

    return essential_stats, 200

# Shows the health of the flask-server.    
@app.route('/health')
def health():
    return "ok", 200

@app.route('/pred_date_options')
def pred_date_options():
    path = PRED_DIR
    filenames = os.listdir(path)
    
    set_year = set()
    set_month = set()
    set_day = set()
    set_hour = set()
    set_minute = set()
    
    for filename in filenames:
        if not filename.endswith('.jpg'):
            continue
        try:
            date_str = filename.split('_date_')[1].replace('_hours_', ' ').replace('.jpg', '')
            dt = datetime.strptime(date_str, "%y-%m-%d %H.%M.%S")
            
            set_year.add(dt.year)
            set_month.add(dt.month)
            set_day.add(dt.day)
            set_hour.add(dt.hour)
            set_minute.add(dt.minute)
        except:
            continue  
        
    return jsonify({
        "years": sorted(list(set_year)),
        "months": sorted(list(set_month)),
        "days": sorted(list(set_day)),
        "hours": sorted(list(set_hour)),
        "minutes": sorted(list(set_minute))
    })


@app.route('/pred_image_list')
def pred_image_list():
    path = PRED_DIR
    filenames_list = list(os.listdir(path))
    
    return filenames_list
    


@app.route('/pred_images_recent')
def pred_images_recent():
    path = PRED_DIR
    files = sorted([f for f in os.listdir(path) 
                   if f.endswith(".jpg") and f.startswith("predicted_")])[-18:]
    
    result = []
    for f in files:
        with open(os.path.join(path, f), 'rb') as img:
            b64 = base64.b64encode(img.read()).decode('utf-8')
            result.append({
                'name': f,
                'data': f'data:image/jpeg;base64,{b64}',
                'time': f.split('hours_')[1].replace('.jpg', '')
            })
    
    return jsonify(result)
    return jsonify(files)

@app.route('/images/<path:filename>')
def serve_image(filename):
    path = PRED_DIR
    return send_from_directory(path, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
