from flask import Flask, request
from PIL import Image, ImageEnhance
import io
import os

app = Flask(__name__)

SAVE_DIR = "captures"
os.makedirs(SAVE_DIR, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload():
    img_bytes = request.data

    if not img_bytes:
        return "No data", 400

    img_type = request.args.get("type", "image")
    raw_path = os.path.join(SAVE_DIR, f"{img_type}.jpg")

    # Save raw image
    with open(raw_path, "wb") as f:
        f.write(img_bytes)

    if img_type == "ir":
        try:
            img = Image.open(io.BytesIO(img_bytes)).convert("L")

            # Boost brightness to compensate for weak IR LEDs
            img = ImageEnhance.Brightness(img).enhance(1.0)

            # Also boost contrast to make the scene more visible
            img = ImageEnhance.Contrast(img).enhance(2.0)

            gray_path = os.path.join(SAVE_DIR, f"{img_type}_gray.jpg")
            img.save(gray_path, "JPEG", quality=95)
            print(f"Saved {raw_path} + enhanced grayscale {gray_path} ({len(img_bytes)} bytes)")
        except Exception as e:
            print(f"Grayscale conversion failed: {e}")
    else:
        print(f"Saved {raw_path} ({len(img_bytes)} bytes)")

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)