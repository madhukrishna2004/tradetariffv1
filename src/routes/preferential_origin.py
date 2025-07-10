import os, shutil, zipfile, tempfile
from flask import Blueprint, request, render_template, session, redirect, flash, url_for, send_file
from werkzeug.utils import secure_filename
from datetime import datetime, date
import pandas as pd
from db import get_db
from preferential_folder_setup import get_user_folder_paths, create_user_folders_if_needed

preferential_origin_bp = Blueprint("preferential_origin", __name__)

# 🔁 Determine shift based on current time
def get_current_shift():
    now = datetime.now().time()
    if now <= datetime.strptime("06:00", "%H:%M").time():
        return "Shift 1"
    elif now <= datetime.strptime("12:00", "%H:%M").time():
        return "Shift 2"
    elif now <= datetime.strptime("18:00", "%H:%M").time():
        return "Shift 3"
    else:
        return "Shift 4"

# 🔁 Simulate PDF generation
def generate_dummy_pdf_report(bom_path, pdf_output_path):
    with open(pdf_output_path, "w") as f:
        f.write(f"PDF Report for {os.path.basename(bom_path)}")

# 🔁 Generate abstract Excel for a shift
def create_shift_abstract(username, shift, export_date, export_files, abstract_path):
    df = pd.DataFrame(export_files, columns=["BoM File", "Export Type", "Report Path"])
    df["Shift"] = shift
    df["Username"] = username
    df["Date"] = export_date
    df.to_excel(abstract_path, index=False)

from datetime import datetime, time

import os
from datetime import datetime
from fpdf import FPDF
import pandas as pd
from db import get_db

def process_and_store_export(username, filename, shift, export_date):
    base_server, base_local = get_user_folder_paths(username)
    
    bom_path = os.path.join(base_local, "BOM_Inputs", filename)

    # PDF & Abstract output folders
    pdf_dir_eu = os.path.join(base_local, "PDFReports", "EU_Preferential")
    abstract_dir = os.path.join(base_local, "AbstractReports")
    os.makedirs(pdf_dir_eu, exist_ok=True)
    os.makedirs(abstract_dir, exist_ok=True)

    # Create dummy PDF
    pdf_file_name = filename.replace(".xlsx", "_YES.pdf")
    pdf_path = os.path.join(pdf_dir_eu, pdf_file_name)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=f"Dummy PDF Export for {filename}", ln=True)
    pdf.output(pdf_path)

    # Save to export_files
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO export_files (username, export_date, shift, export_type, file_name, file_path, export_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (username, export_date, shift, 'EU', pdf_file_name, pdf_path, datetime.now()))
    conn.commit()

    # Also generate abstract (dummy summary)
    abstract_data = {
        "Processed File": [filename],
        "PDF Export": [pdf_file_name],
        "Status": ["Preferential"]
    }
    df = pd.DataFrame(abstract_data)

    abstract_file_name = f"{export_date}_{shift.replace(' ', '_')}_Abstract.xlsx"
    abstract_path = os.path.join(abstract_dir, abstract_file_name)
    df.to_excel(abstract_path, index=False)

    # Save abstract file to export_files (optional)
    cur.execute("""
        INSERT INTO export_files (username, export_date, shift, export_type, file_name, file_path, export_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (username, export_date, shift, 'ABSTRACT', abstract_file_name, abstract_path, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def get_current_shift():
    now = datetime.now().time()
    if time(0, 0) <= now <= time(6, 0):
        return 'Shift 1'
    elif time(6, 1) <= now <= time(12, 0):
        return 'Shift 2'
    elif time(12, 1) <= now <= time(18, 0):
        return 'Shift 3'
    else:
        return 'Shift 4'

@preferential_origin_bp.route("/upload", methods=["GET", "POST"])
def upload_bom():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]
    create_user_folders_if_needed(username)

    if request.method == "POST":
        files = request.files.getlist("bom_file")
        if not files:
            flash("No files selected.")
            return redirect(url_for("preferential_origin.upload_bom"))

        shift = get_current_shift()
        upload_date = datetime.now().date()

        conn = get_db()
        cur = conn.cursor()

        for file in files:
            if file and file.filename.endswith(".xlsx"):
                filename = secure_filename(file.filename)
                base_server, base_local = get_user_folder_paths(username)

                local_path = os.path.join(base_local, "BOM_Inputs", filename)
                server_path = os.path.join(base_server, "BOM_Inputs", filename)

                file.save(local_path)
                shutil.copy(local_path, server_path)

                # Insert into bom_uploads with shift and date
                cur.execute("""
                    INSERT INTO bom_uploads (username, original_filename, saved_path, server_path, shift, upload_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (username, filename, local_path, server_path, shift, upload_date))

                # 🚀 Optional: Trigger processing logic here
                process_and_store_export(username, filename, shift, upload_date)

        conn.commit()
        cur.close()
        conn.close()

        flash("BoM files uploaded and recorded successfully.")
        return redirect(url_for("preferential_origin.upload_bom"))

    return render_template("preferential_origin_upload.html")


# ✅ Export Dashboard
@preferential_origin_bp.route("/exports", methods=["GET"])
def show_exports():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]
    selected_date = request.args.get("date") or date.today().strftime("%Y-%m-%d")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT shift, export_type, file_name, file_path
        FROM export_files
        WHERE username = %s AND export_date = %s
        ORDER BY shift, export_type, export_timestamp DESC
    """, (username, selected_date))
    files = [dict(shift=row[0], export_type=row[1], file_name=row[2], file_path=row[3]) for row in cur.fetchall()]
    cur.close()
    conn.close()

    # Check for existing abstracts per shift
    base_local = get_user_folder_paths(username)[1]
    abstracts = {}
    for shift in ["Shift 1", "Shift 2", "Shift 3", "Shift 4"]:
        path = os.path.join(base_local, "AbstractReports", f"Abstract_{shift}_{selected_date}.xlsx")
        if os.path.exists(path):
            abstracts[shift] = path

    return render_template("exports_dashboard.html", files=files, date=selected_date, abstracts=abstracts)

# ✅ File Download
@preferential_origin_bp.route("/download-file")
def download_file():
    path = request.args.get("file_path")
    if not path or not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True)

# ✅ Download shift files ZIP
@preferential_origin_bp.route("/download-shift", methods=["POST"])
def download_shift():
    if "user" not in session:
        return redirect("/login")
    
    shift = request.form.get("shift")
    date_selected = request.form.get("date")
    username = session["user"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT file_name, file_path FROM export_files
        WHERE username = %s AND export_date = %s AND shift = %s
    """, (username, date_selected, shift))
    files = cur.fetchall()
    cur.close()
    conn.close()

    if not files:
        return "No files found", 404

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        with zipfile.ZipFile(tmp.name, "w") as zipf:
            for fname, fpath in files:
                if os.path.exists(fpath):
                    zipf.write(fpath, arcname=fname)
        return send_file(tmp.name, as_attachment=True, download_name=f"{date_selected}_{shift}_Exports.zip")

# ✅ Download all day ZIP
@preferential_origin_bp.route("/download-day", methods=["POST"])
def download_day():
    if "user" not in session:
        return redirect("/login")

    date_selected = request.form.get("date")
    username = session["user"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT file_name, file_path FROM export_files
        WHERE username = %s AND export_date = %s
    """, (username, date_selected))
    files = cur.fetchall()
    cur.close()
    conn.close()

    if not files:
        return "No files for selected date", 404

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        with zipfile.ZipFile(tmp.name, "w") as zipf:
            for fname, fpath in files:
                if os.path.exists(fpath):
                    zipf.write(fpath, arcname=fname)
        return send_file(tmp.name, as_attachment=True, download_name=f"{date_selected}_All_Shifts_Exports.zip")
@preferential_origin_bp.route("/trigger-abstract", methods=["POST"])
def trigger_shift_abstract():
    if "user" not in session:
        return redirect("/login")

    shift = request.form.get("shift")
    export_date = request.form.get("date")
    username = session["user"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT file_name, export_type, file_path FROM export_files
        WHERE username = %s AND export_date = %s AND shift = %s
    """, (username, export_date, shift))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        flash(f"⚠️ No export files found for {shift} on {export_date}.")
        return redirect(url_for("preferential_origin.show_exports", date=export_date))

    export_records = [[row[0], row[1], row[2]] for row in rows]
    base_local = get_user_folder_paths(username)[1]
    abstract_path = os.path.join(base_local, "AbstractReports", f"Abstract_{shift}_{export_date}.xlsx")
    create_shift_abstract(username, shift, export_date, export_records, abstract_path)

    flash(f"✅ Abstract for {shift} regenerated successfully.")
    return redirect(url_for("preferential_origin.show_exports", date=export_date))


from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from db import get_db
#from export_generator import process_and_store_export  # Make sure this function exists and is imported

def get_shift_name_from_time(current_time):
    hour = current_time.hour
    minute = current_time.minute
    if hour < 6 or (hour == 6 and minute == 0):
        return 'Shift 1'
    elif hour < 12 or (hour == 12 and minute == 0):
        return 'Shift 2'
    elif hour < 18 or (hour == 18 and minute == 0):
        return 'Shift 3'
    else:
        return 'Shift 4'

def process_completed_shift():
    now = datetime.now()
    completed_shift_time = now - timedelta(minutes=1)  # Small buffer
    shift = get_shift_name_from_time(completed_shift_time)

    date_str = completed_shift_time.date()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT username, original_filename
        FROM bom_uploads
        WHERE shift = %s AND upload_date = %s
    """, (shift, date_str))

    files = cur.fetchall()
    if not files:
        print(f"[{datetime.now()}] No files for {shift} on {date_str}")
    else:
        print(f"[{datetime.now()}] Auto-processing {len(files)} files for {shift}")
        for username, filename in files:
            process_and_store_export(username, filename, shift, date_str)

    cur.close()
    conn.close()
