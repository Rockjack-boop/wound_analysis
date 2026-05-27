import os
import uuid
import time
from flask import (
    Flask, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    flash, 
    session, 
    jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Database and Model Imports
from database.db import (
    init_db,
    register_user,
    get_user_by_username,
    get_user_by_id,
    get_all_users,
    add_report,
    get_reports_by_user_id,
    get_all_reports,
    get_report_by_id,
    delete_report,
    get_dashboard_stats
)
from model.predictor import analyze_wound_image
from c_modules.image_processor import get_library_status, process_sobel_edges

# Initialize Flask App
app = Flask(__name__)
app.secret_key = "wound_ai_secure_token_secret_key"

# Configuration
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 Megabyte limit

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(app.root_path, "static", "processed"), exist_ok=True)

# Initialize Database Schema
init_db()

# ----------------------------------------------------
# Security Helpers / Decotators
# ----------------------------------------------------
def allowed_file(filename):
    """Verifies that uploaded file has an allowed JPG/PNG extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def is_logged_in():
    """Checks if the user has a valid active session."""
    return "user_id" in session

def login_required(f):
    """Decorator to protect routes requiring authentication."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash("Authorization required. Please log in first.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to protect administrative panels."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash("Authorization required. Please log in first.", "danger")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Access denied. Administrator privileges required.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function

# ----------------------------------------------------
# Main Web App Routes
# ----------------------------------------------------

@app.route("/")
def home():
    """Renders the website landing page."""
    c_status = get_library_status()
    return render_template("index.html", c_status=c_status)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles new patient and admin registrations."""
    if is_logged_in():
        return redirect(url_for("upload"))
        
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user") # Standard register is 'user', admins created manually or via seed
        
        # Validation checks
        if not username or not email or not password:
            flash("All fields are mandatory. Please try again.", "warning")
            return render_template("register.html")
            
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
            return render_template("register.html")
            
        hashed_password = generate_password_hash(password)
        
        # Insert user to database
        success = register_user(username, email, hashed_password, role)
        if success:
            flash("Account created successfully! You can now log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Username already taken. Please choose another one.", "danger")
            
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticates users and establishes sessions."""
    if is_logged_in():
        return redirect(url_for("upload"))
        
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            flash("Please input both username and password.", "warning")
            return render_template("login.html")
            
        user = get_user_by_username(username)
        
        # Verify user exists and check hashed password
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            
            flash(f"Welcome back, {user['username']}!", "success")
            
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("upload"))
        else:
            flash("Invalid credentials. Please verify and try again.", "danger")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Destroys current user sessions."""
    session.clear()
    flash("Successfully logged out. Stay safe!", "success")
    return redirect(url_for("home"))

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """Handles image uploads and triggers the C-assisted AI classification."""
    if request.method == "POST":
        # Check if file part is in request
        if "wound_image" not in request.files:
            flash("No file part provided in the request.", "warning")
            return redirect(request.url)
            
        file = request.files["wound_image"]
        
        if file.filename == "":
            flash("No image file selected for analysis.", "warning")
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            # Secure filename generation to avoid path injections
            filename = secure_filename(file.filename)
            unique_prefix = uuid.uuid4().hex[:10]
            secure_name = f"{unique_prefix}_{filename}"
            
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_name)
            file.save(save_path)
            
            try:
                # Trigger C-assisted image feature extraction & diagnostic profiling
                report_data = analyze_wound_image(save_path, os.path.join(app.root_path, "static"))
                
                # Save report in the SQLite database
                report_id = add_report(
                    user_id=session["user_id"],
                    filename=secure_name,
                    wound_type=report_data["wound_type"],
                    severity=report_data["severity"],
                    major_minor=report_data["major_minor"],
                    infection_possibility=report_data["infection_possibility"],
                    emergency_level=report_data["emergency_level"],
                    confidence=report_data["confidence"],
                    first_aid=report_data["first_aid"],
                    red_pixel_count=report_data["metrics"]["red_pixels"],
                    redness_ratio=report_data["metrics"]["redness_ratio"]
                )
                
                flash("Wound diagnostic completed successfully!", "success")
                return redirect(url_for("result", report_id=report_id))
                
            except Exception as e:
                flash(f"An error occurred during C-AI processing: {e}", "danger")
                return redirect(request.url)
        else:
            flash("Invalid format. Please upload a standard JPG, JPEG, or PNG image.", "danger")
            return redirect(request.url)
            
    return render_template("upload.html")

@app.route("/result/<int:report_id>")
@login_required
def result(report_id):
    """Displays the AI Diagnostic Report Dashboard."""
    report = get_report_by_id(report_id)
    
    if not report:
        flash("The requested report could not be found.", "warning")
        return redirect(url_for("history"))
        
    # Security check: User must own the report, or be an admin
    if report["user_id"] != session["user_id"] and session.get("role") != "admin":
        flash("Access Denied. You do not have permissions to view this report.", "danger")
        return redirect(url_for("history"))
        
    # Split first aid guidelines into clean bullet point arrays
    first_aid_bullets = report["first_aid"].split("||")
    
    # Reconstruct filenames for visualization
    filename = report["filename"]
    base_name, ext = os.path.splitext(filename)
    
    visuals = {
        "original": f"uploads/{filename}",
        "gray": f"processed/{base_name}_gray{ext}",
        "sobel": f"processed/{base_name}_sobel{ext}",
        "redness": f"processed/{base_name}_redness{ext}"
    }
    
    return render_template(
        "result.html", 
        report=report, 
        first_aid_bullets=first_aid_bullets,
        visuals=visuals
    )

@app.route("/history")
@login_required
def history():
    """Renders the patient's chronological history timeline."""
    reports = get_reports_by_user_id(session["user_id"])
    return render_template("history.html", reports=reports)

@app.route("/history/delete/<int:report_id>", methods=["POST"])
@login_required
def delete_history_report(report_id):
    """Deletes a diagnostic record from history."""
    report = get_report_by_id(report_id)
    if not report:
        flash("Report not found.", "warning")
        return redirect(url_for("history"))
        
    # Security: Must be owner or admin
    if report["user_id"] != session["user_id"] and session.get("role") != "admin":
        flash("Unauthorized deletion attempt.", "danger")
        return redirect(url_for("history"))
        
    delete_report(report_id)
    
    # Try to delete original files from static directory if they exist to keep space tidy
    filename = report["filename"]
    base_name, ext = os.path.splitext(filename)
    
    files_to_delete = [
        os.path.join(app.config["UPLOAD_FOLDER"], filename),
        os.path.join(app.root_path, "static", "processed", f"{base_name}_gray{ext}"),
        os.path.join(app.root_path, "static", "processed", f"{base_name}_sobel{ext}"),
        os.path.join(app.root_path, "static", "processed", f"{base_name}_redness{ext}")
    ]
    
    for f in files_to_delete:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
                
    flash("Diagnostic report record deleted permanently.", "success")
    return redirect(url_for("history"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    """Renders the analytic system monitoring dashboard for administrators."""
    stats = get_dashboard_stats()
    users = get_all_users()
    reports = get_all_reports()
    c_status = get_library_status()
    
    return render_template(
        "admin.html", 
        stats=stats, 
        users=users, 
        reports=reports,
        c_status=c_status
    )

# ----------------------------------------------------
# Interactive AJAX Preview API for Upload Page
# ----------------------------------------------------
@app.route("/api/preprocess-preview", methods=["POST"])
@login_required
def preprocess_preview():
    """
    Accepts an uploaded image and performs instant C-based Sobel preprocessing,
    returning the base64 or temporary URL link. Facilitates real-time UX previews.
    """
    if "wound_image" not in request.files:
        return jsonify({"success": False, "error": "No file part in request."}), 400
        
    file = request.files["wound_image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        temp_name = f"temp_preview_{uuid.uuid4().hex[:6]}_{filename}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], temp_name)
        file.save(save_path)
        
        base_name, ext = os.path.splitext(temp_name)
        sobel_name = f"{base_name}_sobel{ext}"
        sobel_path = os.path.join(app.root_path, "static", "processed", sobel_name)
        
        try:
            # Trigger Sobel preprocessing exclusively
            sobel_res = process_sobel_edges(save_path, sobel_path)
            
            # Clean up original temp file immediately to save disk
            if os.path.exists(save_path):
                os.remove(save_path)
                
            return jsonify({
                "success": True,
                "preview_url": url_for("static", filename=f"processed/{sobel_name}"),
                "c_mode": sobel_res["mode"],
                "duration_ms": sobel_res["time_ms"]
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
            
    return jsonify({"success": False, "error": "Invalid file extension format."}), 400

if __name__ == "__main__":
    print("[Server] Starting Wound AI Flask Application...")
    app.run(debug=True, host="127.0.0.1", port=5000)
