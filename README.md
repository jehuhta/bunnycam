
# Bunnycam
<h3><i>Computer Vision Rabbit Health Monitoring System</i></h3>

<p>An amateur project from a <strong>Machine Learning & Data Engineering</strong> student developer, built to solve a real problem: early detection of GI stasis in pet rabbits — a condition that can be fatal within hours if left untreated.</p>

<br>
<br>



<div align="center">

### <i> WORK IN PROGRESS </i>

  <br>
  <br>
  
  
  <img width="1054" height="622" alt="image" src="https://github.com/user-attachments/assets/a3c04e3d-8133-404c-8809-33070ffec9d0" />
  
  <img width="721" height="696" alt="image" src="https://github.com/user-attachments/assets/23dff2ea-df2a-4f7a-91a4-ce99ba1e1a03" />
  
  <img width="242" height="340" alt="image" src="https://github.com/user-attachments/assets/b9f37ab5-0366-4898-8020-a9833cc820c0" />
  
  <img width="1225" height="322" alt="image" src="https://github.com/user-attachments/assets/fe6db3ba-91a3-4911-b820-fd1f6b46c5a4" />
  
  <br>
  <br>



</div>


<br>
<br>
<br>

---

### <ins>The Problem</ins>

Rabbits are prone to **GI stasis**, a life-threatening condition where their digestive system slows or stops. Early detection is critical — one of the key indicators is a rabbit not visiting their litter box. This system monitors litter box visits **24/7** and alerts owners when intervention may be needed, making it a great supplement for rabbit health-monitoring.

<br>

---

### <ins>Features</ins>

- **AI-powered detection** — YOLO11s model identifies individual rabbits by name in real time
- **Automated health alerts** — notifies owner's phones if a rabbit hasn't visited the litter box within a configurable time window
- **Interactive dashboard** — live camera feed, visit history, statistics, and device status, accessible from anywhere in the world
- **Image gallery** — browse and filter historical camera frames by date and time
- **Dark mode & theming** — Vuetify-powered UI with user-controlled theme switching
- **Privacy first** — all data stays on your own hardware, no third-party cloud services

<br>

---

### <ins>Architecture</ins>

<div align="center">
ESP32-S3 Cameras (WiFi)
→ Flask REST API (Raspberry Pi 5)
→ YOLO11s Inference
→ DuckDB (predictions, scores, visit history)
→ Node-RED Dashboard (frontend)
→ Cloudflare Tunnel (public HTTPS access)
</div>

<br>


- **ESP32-S3 FireBeetle** microcontrollers with OV2640 cameras send JPEG frames over WiFi via HTTP
- **ESP32 WROOM** controls 850nm IR LED lighting for reliable night vision *(invisible to rabbits and humans)*
- **Raspberry Pi 5** runs Flask for inference, Node-RED for the dashboard, and DuckDB for storage
- **YOLO11s** model trained on *~3500 manually annotated images* via Label Studio
- **Exponential decay scoring system** — prevents false positives by requiring sustained detections before triggering alerts
- **Cloudflare Tunnel + Zero Trust Access** — secure public HTTPS with email-based authentication, no port forwarding required

<br>

---

### <ins>Stack</ins>

| Component | Technology |
|---|---|
| Object Detection | YOLO11s (Ultralytics) |
| Annotation | Label Studio |
| Backend | Python, Flask |
| Database | DuckDB |
| Frontend | Node-RED Dashboard 2.0 (Vue/Vuetify) |
| Microcontrollers | ESP32-S3, ESP32 WROOM |
| Hosting | Cloudflare Tunnel |
| Hardware | Raspberry Pi 5 |

<br>

---

### <ins>Budget</ins>

Total build cost under **200 EUR**, including:
- Raspberry Pi 5
- ESP32-S3 camera modules
- ESP32 WROOM IR controllers
- 850nm IR LED strips
- Storage & miscellaneous hardware

<br>

---

### <ins>Use-case</ins>

Commercial pet monitoring solutions are *expensive*, *cloud-dependent*, and *not designed for rabbits* specifically. This project prioritises **privacy**, **affordability**, and **full ownership of your data** — while solving a genuinely useful problem for rabbit owners.

---

<div align="center">
<i>Built with care for Aune and Dippi.</i>
</div>
