# WoundAI - AI-Powered Wound Detection and Severity Classification Platform

WoundAI is a complete, medical-themed diagnostic web platform utilizing a secure **Python-Flask** backend combined with a high-performance **compiled C module** linked via `ctypes` for real-time image processing (grayscale mapping, Sobel edge gradients, and inflammation redness profiling). 

---

## 🔬 System Architecture

The platform has been designed to operate as a high-performance, secure clinical console. It binds Python’s powerful database and network capabilities with the fast execution speed of C.

```
                  ┌────────────────────────────────────────┐
                  │          Flask Web Interface           │
                  │   (Home, Upload, Reports, Admin)       │
                  └──────────────────┬─────────────────────┘
                                     │
                        Calls Preprocessing APIs
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │       ctypes Integration Layer         │
                  │     (c_modules/image_processor.py)      │
                  └──────────────────┬─────────────────────┘
                                     │
                        Maps image bytes to C pointers
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │        Compiled C Library Core         │
                  │     (c_modules/image_processor.c)      │
                  │   [DLL Binary / NumPy-Accelerated]     │
                  └──────────────────┬─────────────────────┘
                                     │
                        Feeds structural features to
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │           AI Predictor Engine          │
                  │          (model/predictor.py)          │
                  └────────────────────────────────────────┘
```

### 🛠️ Folder Structure
- `templates/` — Clean, structured Jinja2 templates (Home, Upload, Results, History, Admin Dashboard).
- `static/` — Diagnostic outputs, uploaded files, and custom CSS styling.
- `static/css/style.css` — High-end dark clinical style utilizing glassmorphism, HSL custom variables, and animations.
- `uploads/` — Secure storage directory for original user-uploaded photographs.
- `model/` — AI model simulator combining C redness index and edge densities.
- `database/` — SQLite configuration layer, auto-migrations, and user queries.
- `c_modules/` — High-performance C filters, automated compilers, and ctypes links.

---

## ⚡ Key Platform Features

1. **C Edge-Detection Pipeline**: Implements the classic **Sobel Gradient Operator** in compiled C to extract structural wound contours in milliseconds.
2. **Infection / Erythema Profiling**: Isolates severe tissue redness (inflammation boundaries) using strict pixel ratio filters, rendering high-contrast medical heatmaps.
3. **Interactive Preprocessing Preview**: Uploading an image asynchronously invokes a preview, running Sobel edge gradients instantly and displaying output to the patient before submission.
4. **Actionable Treatment Checklists**: Generates interactive first aid checklists matched to the classification (e.g. chemical burns vs. lacerations).
5. **Secure Authentication & Admin Console**: Protects reports via session validation, hashing passwords, and tracking performance telemetry on the system console.

---

## 🚀 Installation & Launch Steps

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your host system.

### 2. Install Python Dependencies
Open PowerShell or Terminal in the project root folder and execute:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the local server:
```bash
python app.py
```
The console will automatically scan for compilers (`gcc`, `clang`, or `cl.exe`) to compile `c_modules/image_processor.c` into a shared library.
* **If a compiler is found**: A compiled shared library `image_processor.dll` (on Windows) or `.so` (on Unix) is generated and linked.
* **If no compiler is found**: The system transparently falls back to an identical, optimized **NumPy-accelerated preprocessor** to guarantee the site works **100% end-to-end immediately after installation**.

### 4. Open in Browser
Open your browser and navigate to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔑 Access Credentials

To test both Patient and Clinician viewpoints out-of-the-box, the database seeds a default administrator account automatically upon first initialization:

* **Username**: `admin`
* **Password**: `admin123`

You can also register a standard patient account via the registration page.

---

## 🔒 Security Best Practices Implemented

- **Password Hashing**: Implements Werkzeug scrypt hashing to ensure patient credentials are safe.
- **SQL Injection Prevention**: Uses parameterized SQLite commands exclusively.
- **Session Validation**: All diagnostic results and historical routes are protected by cookie session tokens. Users cannot read another patient's medical reports.
- **Secure File Handling**: Enforces file size limitations (Max 10MB) and strict JPG/PNG extension checks with uuid-obfuscated filename generation to block path traversal vulnerabilities.
