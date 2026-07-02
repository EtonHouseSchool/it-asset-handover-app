import os
import io
import json
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from config import Config
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from sqlalchemy import text
import db

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get("SECRET_KEY", "MarwenSuperSecret2025")
mail = Mail(app)

# ── Auth ──
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

_ACCOUNTS = {
    "marwen": os.environ.get("ADMIN_PASSWORD_HASH", ""),
    "backup": os.environ.get("BACKUP_PASSWORD_HASH", ""),
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id in _ACCOUNTS:
        return User(user_id)
    return None

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").encode()
        stored_hash = _ACCOUNTS.get(username, "").encode()
        if stored_hash and bcrypt.checkpw(password, stored_hash):
            login_user(User(username), remember=True)
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

CAMPUSES = {"EISG": "K12 School", "EIPSG": "Preschool", "HQ": "HQ Team", "EIEA": "HQ Team"}
ASSET_TYPES = ["Laptop", "Monitor", "iPad", "Desktop PC", "IP Phone"]
STATUSES = ["Assigned", "In Store", "Lost/Stolen", "Returned", "Under Repair"]


def seed_data():
    if db.is_seeded():
        return

    def ins(asset_type, serial, assigned_to, campus, issued, remarks, email, ack,
            model="", part="", location="", status="Assigned", batch="", ip="", ext="", creds=""):
        campus_val = campus if campus in CAMPUSES else "HQ"
        if status == "Assigned" and (not assigned_to or assigned_to.strip() in ["", "\xa0"]):
            status = "In Store"
        with db._engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assets (asset_type, serial_number, part_number, model_name,
                    assigned_to, campus, issued_date, location, remarks, email_sent,
                    acknowledgement, status, batch, ip_address, extension, credentials)
                VALUES (:at,:sn,:pn,:mn,:ao,:ca,:id,:lo,:re,:em,:ac,:st,:ba,:ip,:ex,:cr)
            """), dict(at=asset_type, sn=serial, pn=part, mn=model, ao=assigned_to,
                       ca=campus_val, id=str(issued) if issued else "", lo=location,
                       re=remarks or "", em=email or "", ac=ack or "", st=status,
                       ba=batch, ip=ip, ex=str(ext) if ext else "", cr=creds))
            conn.commit()

    # ── Laptops Batch 1 ──
    for row in [
        ("PF-5FAWEL","Farah Abou Alfa","HQ",None,"Confirmed"),
        ("PF-5F8AJ2","Mohammad Al Sharif","HQ",None,"Confirmed"),
        ("PF-5FAWAV","Connor-Scahill Elizabeth Denise","EIPSG",None,"Confirmed"),
        ("PF-5FAXRH","Shaqeel Said","EISG",None,"Confirmed"),
        ("PF-5FAWD0","Erika Berintingane","EISG",None,"Confirmed"),
        ("PF-5FASLZ","Sally Darazi","HQ",None,"Confirmed"),
        ("PF-5FASLB","Saeed Alkhaleed","HQ","2025-03-01","Confirmed"),
        ("PF-5FAXSS","SAHAR AL Sababagh","HQ",None,"Confirmed"),
        ("PF-5FAWC5","Naziha Mardam","EIPSG","2025-08-11","Pre school teacher"),
        ("PF-5F889H","Marwan Bin Khalifa","HQ","2025-08-19","Confirmed"),
    ]:
        ins("Laptop",row[0],row[1],row[2],row[3],row[4],"Done","",batch="Batch 1")
    ins("Laptop","PF-5CA55G","Anas Haswah","HQ","2026-01-14",
        "Stolen from the user near Granada Flow","Done","",batch="Batch 1",status="Lost/Stolen")

    # ── Laptops Batch 2 ──
    for row in [
        ("PF-5FAWD0","Erika Berintingane","EISG","2026-04-14","Confirmed"),
        ("PF-5D9J0B","Chelsea Jones","EISG","2025-07-20","Confirmed"),
        ("PF-5D6Z3K","Teresa Van Der Linde","EISG","2025-07-20","Confirmed"),
        ("PF-5C90DG","Natasha","EIPSG","2025-07-20","Pre school teacher"),
        ("PF-5C8VSR","Sadia Sidd","EIEA","2025-08-03","HQ assigned from school batch"),
        ("PF-5C8VXP","Hollie Tickle","EIPSG",None,"Confirmed"),
        ("PF-5CA58L","Meshal Al Otaibi","EISG","2025-07-31","Confirmed"),
        ("PF-5C90EQ","Yasmin Rashid","EIPSG","2025-07-31","Pre school teacher"),
        ("PF-5D9HZJ","Daniya Natha","EISG","2025-07-31","Confirmed"),
        ("PF-5CA57X","Twane Coaker","EISG","2025-08-03","Confirmed"),
        ("PF-5A8GB5","Rosol Muqbel","EISG","2025-08-10","Confirmed"),
        ("PF-5C8VSK","Amina Reguti","EISG","2025-08-10","Confirmed"),
        ("PF-5D6Z5S","Teresa Ma (nurse)","EISG","2025-08-10","Confirmed"),
        ("PF-5C8VWL","Moncef Abelualli","EISG","2025-08-07","Confirmed"),
        ("PF-5CA2Y3","Yasmeen Begum","EISG","2025-08-03","Confirmed"),
        ("PF-5A8Z41","Simon Gilroy","EISG","2025-08-17","Confirmed"),
        ("PF-5CA7CX","Atheer Al Anzan","EIPSG","2025-08-05","Pre school teacher"),
    ]:
        ins("Laptop",row[0],row[1],row[2],row[3],row[4],"Done","",batch="Batch 2")

    # ── Laptops Batch 3 ──
    for row in [
        ("PF-5SA3GF","Hodo Ali","EIPSG","2026-01-07","N/A"),
        ("PF-5S4JGV","Jacqueline Nahirney","EISG","2026-01-07","N/A"),
        ("PF-5RLFGT","Anas Haswah","HQ","2026-01-19","N/A"),
        ("PF-5S9TMB","Sarah AlGraishah","HQ","2025-12-10","N/A"),
        ("PF-5S3WEV","Muhib Ur Rahman","HQ","2026-01-10","N/A"),
        ("PF-5SA3J3","Reenad Shaik","HQ","2025-10-22","N/A"),
    ]:
        ins("Laptop",row[0],row[1],row[2],row[3],row[4],"Done","",batch="Batch 3")

    # ── Laptops Batch 4 ──
    ins("Laptop","PF5RLFGT","Anas Haswah","HQ","2026-01-15",
        "Replacement laptop following theft. Handed to manager Mohammad Alsharif.","Done","",batch="Batch 4")
    ins("Laptop","PF5XTPF2","Gaelin Brown","EISG","2026-01-29",None,"Done","Done",batch="Batch 4")

    # ── Laptops Batch 5 ──
    for row in [
        ("PF68A22Y","Huda Alamari","EIPSG","2026-05-07","Noor admin"),
        ("PF68952B","Vildana Dupanovich","EISG","2026-05-20","K12 principal"),
        ("PF6876W3","Anne Marie","HQ","2026-06-18","Director of Education"),
        ("PF5XEEY1R","Shaqeel Said","HQ",None,"CEO"),
    ]:
        ins("Laptop",row[0],row[1],row[2],row[3],row[4],"","",batch="Batch 5")

    # ── Monitors ──
    for row in [
        ("VN-0WPMX8-WS700-51G-033B-A03","Marwen Ben Khalifa","HQ","Batch 1"),
        ("CN-0XT1N5-TV200-53J-12CT-A00","Farah Abu Alfa","HQ","Batch 1"),
        ("27462054784","Shaqeel Said","HQ","Batch 1"),
        ("VN-0WPMX8-WS700-51G-108B-A03","Rain Jones","HQ","Batch 1"),
        ("VN-0WPMXB-WS700-51G-221B-A03","Rayyan Mahmood","HQ","Batch 3"),
        ("CN-0XT1N5-TV200-53J-0QHT-A00","Sadia Siddique","HQ","Batch 3"),
        ("VN-0WPMXB-WS700-51G-864B-A03","Anas Haswah","HQ","Batch 1"),
        ("VN-0WPMXB-WS700-51G-891B-A03","Mohammed Alsharif","HQ","Batch 1"),
        ("VN-0WPMXB-WS700-51G-256B-A03","Reenad","HQ","Batch 1"),
        ("3940712320","Saeed Alkhaled","HQ","Batch 1"),
        ("43062328192","Nada Alshehri","HQ","Batch 1"),
        ("CN-0XT1N5-TV200-53J-0W0T-A00","Sarah","HQ","Batch 3"),
        ("CN-0XT1N5-TV200-53J-0MUT-A00","Meshal AlOtaibi","HQ","Batch 3"),
        ("VN-0WPMX8-WS700-51G-177B-A03","Elizabeth Connor","EIPSG","Batch 1"),
        ("CN-0XT1N5-TV200-53J-12HT-A00","Muhib Ur Rahman","HQ","Batch 3"),
        ("CN-0XT1N5-TV200-54S-165T","IT Store","EIPSG","Batch 4"),
    ]:
        ins("Monitor",row[0],row[1],row[2],None,None,None,None,
            batch=row[3],status="In Store" if row[1]=="IT Store" else "Assigned")

    # ── iPads ──
    for row in [
        ("SD99WMJ9W39","Hanan Almusaily","EISG",None),
        ("SFWHCWC123L","Bron","EIPSG","Preschool"),
        ("SJXJLYP2WNN","IT Store","EISG",None),
        ("SK21QYGQPFX","Rosol Moqbel","EISG",None),
        ("SKG5LXN10VM","Ayesha Gilroy","EISG",None),
        ("SKR934Y34DK","Moncef Abdellawi","EISG",None),
        ("SL3369CC42Y","Yunjie Sun","EISG",None),
        ("SFQVDXW1610","Simon Gilroy","EISG",None),
        ("SH6PYPYD4VD","Yasmin Mohamed","EISG",None),
        ("SCXLG9GY045","Yasmeen Begum","EISG","K12-Library"),
        ("SDJWR29FY9C","Natasha Veronika","EIPSG",None),
        ("SG909J07Q4K","Teresa Lambrechts","EISG",None),
        ("SH2TV6XG2QY","Yasmin Rashid","EIPSG","Preschool"),
        ("SJ23T775144","Elanie Van Der Nest","EIPSG","Preschool"),
        ("SJY71XCGWJR","Aisha Mirza","EIPSG","Preschool"),
        ("SK23WT3J9KY","Halima Khanom","EIPSG","Preschool"),
    ]:
        ins("iPad",row[0],row[1],row[2],None,None,"yes","yes",
            model="iPad WiFi 256GB SLV-SAU",part="MD4G4AB/A",
            location=row[3] or "",status="In Store" if row[1]=="IT Store" else "Assigned")

    # ── Desktop PCs ──
    for row in [
        ("7M9JKC4","Preschool Principal office","EIPSG","B2","DELL ALL IN ONE"),
        ("JNRDJ84","K12 reception","EISG","B2",""),
        ("FMRDJ84","K12 Library","EISG","B3",""),
        ("8M9JKC4","K12 Library","EISG","B3",""),
        ("DK9JKC4","K12 Library","EISG","B3",""),
        ("4M9JKC4","K12 Library","EISG","B3",""),
        ("1HF51208YM","K12/Security Area","EISG","B2","HP ProDesk"),
        ("DAEV3KJY9008","K12/Security Area - TV Samsung 55\"","EISG","B2","Samsung 55\" UA55DUE800UXSA"),
    ]:
        ins("Desktop PC",row[0],None,row[2],None,None,None,None,
            model=row[4],location=row[1],batch=row[3],status="Assigned")

    # ── IP Phones ──
    for row in [
        ("10.200.40.1","","EISG","Gateway","admin, Ab123456++"),
        ("10.200.40.2","100","EISG","Reception K12","admin, Ab123456++"),
    ]:
        ins("IP Phone",f"IP:{row[0]}",None,row[2],None,None,None,None,
            location=row[3],ip=row[0],ext=row[1],creds=row[4],status="Assigned")


# Initialise DB and seed on startup
db.init_db()
seed_data()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def query(sql, params=None):
    with db._engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return db.rows_as_dicts(result)


def execute(sql, params=None):
    with db._engine.connect() as conn:
        conn.execute(text(sql), params or {})
        conn.commit()


def scalar(sql, params=None):
    with db._engine.connect() as conn:
        return conn.execute(text(sql), params or {}).scalar()


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
@app.route("/")
@login_required
def dashboard():
    total = scalar("SELECT COUNT(*) FROM assets")
    by_type = {r["asset_type"]: r["cnt"] for r in query("SELECT asset_type, COUNT(*) cnt FROM assets GROUP BY asset_type")}
    by_campus = {r["campus"]: r["cnt"] for r in query("SELECT campus, COUNT(*) cnt FROM assets GROUP BY campus")}
    by_status = {r["status"]: r["cnt"] for r in query("SELECT status, COUNT(*) cnt FROM assets GROUP BY status")}
    recent_assets = query("SELECT * FROM assets ORDER BY id DESC LIMIT 8")

    campus_labels = {"EISG": "K12 School", "EIPSG": "Preschool", "HQ": "HQ Team"}
    campus_display = {campus_labels.get(k, k): v for k, v in by_campus.items()}

    return render_template("dashboard.html",
                           total=total, by_type=by_type,
                           campus_display=campus_display, by_status=by_status,
                           recent_assets=recent_assets,
                           by_type_json=json.dumps(by_type),
                           campus_json=json.dumps(campus_display),
                           status_json=json.dumps(by_status))


# ─────────────────────────────────────────────
# ASSETS LIST
# ─────────────────────────────────────────────
@app.route("/assets")
@login_required
def assets():
    asset_type = request.args.get("type", "")
    campus     = request.args.get("campus", "")
    status     = request.args.get("status", "")
    q          = request.args.get("q", "")

    sql = "SELECT * FROM assets WHERE 1=1"
    params = {}
    if asset_type: sql += " AND asset_type=:at";     params["at"] = asset_type
    if campus:     sql += " AND campus=:ca";          params["ca"] = campus
    if status:     sql += " AND status=:st";          params["st"] = status
    if q:
        like = "ILIKE" if "postgresql" in db._DATABASE_URL else "LIKE"
        sql += f" AND (serial_number {like} :q OR assigned_to {like} :q OR model_name {like} :q)"
        params["q"] = f"%{q}%"
    sql += " ORDER BY id DESC"

    rows = query(sql, params)
    return render_template("assets.html", rows=rows, asset_types=ASSET_TYPES,
                           campuses={"EISG":"K12 School","EIPSG":"Preschool","HQ":"HQ Team"},
                           statuses=STATUSES, current_type=asset_type,
                           current_campus=campus, current_status=status, current_q=q)


# ─────────────────────────────────────────────
# ADD / EDIT ASSET
# ─────────────────────────────────────────────
@app.route("/assets/add", methods=["GET", "POST"])
@login_required
def add_asset():
    if request.method == "POST":
        f = request.form
        execute("""
            INSERT INTO assets (asset_type, serial_number, part_number, model_name, assigned_to,
                campus, issued_date, location, remarks, email_sent, acknowledgement,
                status, batch, ip_address, extension, credentials)
            VALUES (:at,:sn,:pn,:mn,:ao,:ca,:id,:lo,:re,:em,:ac,:st,:ba,:ip,:ex,:cr)
        """, dict(at=f.get("asset_type"), sn=f.get("serial_number"), pn=f.get("part_number"),
                  mn=f.get("model_name"), ao=f.get("assigned_to"), ca=f.get("campus"),
                  id=f.get("issued_date"), lo=f.get("location"), re=f.get("remarks"),
                  em=f.get("email_sent"), ac=f.get("acknowledgement"), st=f.get("status"),
                  ba=f.get("batch"), ip=f.get("ip_address"), ex=f.get("extension"),
                  cr=f.get("credentials")))
        flash("Asset added successfully!", "success")
        return redirect(url_for("assets"))
    return render_template("add_edit_asset.html", asset=None, asset_types=ASSET_TYPES,
                           campuses={"EISG":"K12 School","EIPSG":"Preschool","HQ":"HQ Team"},
                           statuses=STATUSES)


@app.route("/assets/<int:asset_id>/edit", methods=["GET", "POST"])
@login_required
def edit_asset(asset_id):
    if request.method == "POST":
        f = request.form
        execute("""
            UPDATE assets SET asset_type=:at, serial_number=:sn, part_number=:pn,
                model_name=:mn, assigned_to=:ao, campus=:ca, issued_date=:id,
                location=:lo, remarks=:re, email_sent=:em, acknowledgement=:ac,
                status=:st, batch=:ba, ip_address=:ip, extension=:ex, credentials=:cr
            WHERE id=:xid
        """, dict(at=f.get("asset_type"), sn=f.get("serial_number"), pn=f.get("part_number"),
                  mn=f.get("model_name"), ao=f.get("assigned_to"), ca=f.get("campus"),
                  id=f.get("issued_date"), lo=f.get("location"), re=f.get("remarks"),
                  em=f.get("email_sent"), ac=f.get("acknowledgement"), st=f.get("status"),
                  ba=f.get("batch"), ip=f.get("ip_address"), ex=f.get("extension"),
                  cr=f.get("credentials"), xid=asset_id))
        flash("Asset updated successfully!", "success")
        return redirect(url_for("assets"))
    rows = query("SELECT * FROM assets WHERE id=:id", {"id": asset_id})
    asset = rows[0] if rows else None
    return render_template("add_edit_asset.html", asset=asset, asset_types=ASSET_TYPES,
                           campuses={"EISG":"K12 School","EIPSG":"Preschool","HQ":"HQ Team"},
                           statuses=STATUSES)


@app.route("/assets/<int:asset_id>/delete", methods=["POST"])
@login_required
def delete_asset(asset_id):
    execute("DELETE FROM assets WHERE id=:id", {"id": asset_id})
    flash("Asset deleted.", "info")
    return redirect(url_for("assets"))


@app.route("/assets/<int:asset_id>")
@login_required
def asset_detail(asset_id):
    rows = query("SELECT * FROM assets WHERE id=:id", {"id": asset_id})
    asset = rows[0] if rows else None
    campus_labels = {"EISG":"K12 School","EIPSG":"Preschool","HQ":"HQ Team"}
    return render_template("asset_detail.html", asset=asset, campus_labels=campus_labels)


# ─────────────────────────────────────────────
# HANDOVER FORM
# ─────────────────────────────────────────────
@app.route("/handover", methods=["GET", "POST"])
@login_required
def handover_form():
    if request.method == "POST":
        f = request.form
        execute("""
            INSERT INTO handover (date, employee_name, iqama, job_title, department, campus,
                asset_receipt_date, return_date, notes, item_name, model, serial,
                color, condition, accessories)
            VALUES (:da,:en,:iq,:jt,:de,:ca,:ar,:rd,:no,:it,:mo,:se,:co,:cn,:ac)
        """, dict(da=f.get("date"), en=f.get("employee_name"), iq=f.get("iqama"),
                  jt=f.get("job_title"), de=f.get("department"), ca=f.get("campus"),
                  ar=f.get("asset_receipt_date"), rd=f.get("return_date"), no=f.get("notes"),
                  it=f.get("item_name"), mo=f.get("model"), se=f.get("serial"),
                  co=f.get("color"), cn=f.get("condition"), ac=f.get("accessories")))

        body = (f"New IT Asset Handover\n\nDate: {f.get('date')}\nEmployee: {f.get('employee_name')}\n"
                f"Campus: {f.get('campus')}\nDept: {f.get('department')}\n\n"
                f"Asset: {f.get('item_name')} | {f.get('model')}\nSerial: {f.get('serial')}\n"
                f"Condition: {f.get('condition')}\nAccessories: {f.get('accessories')}\n"
                f"Notes: {f.get('notes')}")
        try:
            mail.send(Message(subject="New IT Asset Handover — EtonHouse",
                              sender=os.environ.get("MAIL_DEFAULT_SENDER","it@etonhouse.com.sa"),
                              recipients=["marwen.khalifa@etonhouse.com.sa"], body=body))
        except Exception as e:
            print("Email error:", e)
        return render_template("submitted.html")

    assets_list = query("SELECT serial_number, assigned_to, asset_type FROM assets WHERE status='Assigned' ORDER BY asset_type")
    return render_template("handover.html",
                           campuses={"EISG":"K12 School","EIPSG":"Preschool","HQ":"HQ Team"},
                           assets_list=assets_list)


# ─────────────────────────────────────────────
# RECORDS
# ─────────────────────────────────────────────
@app.route("/records")
@login_required
def records():
    rows = query("SELECT * FROM handover ORDER BY id DESC")
    return render_template("records.html", rows=rows)


@app.route("/records/<int:record_id>/pdf")
@login_required
def generate_pdf(record_id):
    rows = query("SELECT * FROM handover WHERE id=:id", {"id": record_id})
    if not rows:
        return "Not found", 404
    r = rows[0]

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    pdf.setFillColorRGB(0.08, 0.22, 0.42)
    pdf.rect(0, h - 3.5*cm, w, 3.5*cm, fill=True, stroke=False)
    pdf.setFillColorRGB(1,1,1)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(2*cm, h - 2*cm, "IT Asset Handover Form")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(2*cm, h - 2.8*cm, "EtonHouse International School")
    pdf.setFillColorRGB(0,0,0)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(2*cm, h - 4.5*cm, f"Record ID: #{r['id']}    Date: {r['date']}")

    def section_title(y, label):
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColorRGB(0.08, 0.22, 0.42)
        pdf.drawString(2*cm, y, label)
        pdf.setFillColorRGB(0,0,0)

    def make_table(data, y):
        t = Table(data, colWidths=[6*cm, 12*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#14375C")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f0f4f8")]),
        ]))
        t.wrapOn(pdf, w, h)
        t.drawOn(pdf, 2*cm, y)

    section_title(h - 5.8*cm, "Employee Information")
    make_table([
        ["Field","Details"],
        ["Employee Name", r.get("employee_name","")],
        ["ID / Iqama", r.get("iqama","")],
        ["Job Title", r.get("job_title","")],
        ["Department / Campus", f"{r.get('department','')} | {r.get('campus','')}"],
        ["Asset Receipt Date", r.get("asset_receipt_date","")],
        ["Return Date", r.get("return_date","")],
        ["Notes", r.get("notes","")],
    ], h - 13*cm)

    section_title(h - 14.2*cm, "Asset Information")
    make_table([
        ["Field","Details"],
        ["Item Name", r.get("item_name","")],
        ["Model", r.get("model","")],
        ["Serial Number", r.get("serial","")],
        ["Color", r.get("color","")],
        ["Condition", r.get("condition","")],
        ["Accessories", r.get("accessories","")],
    ], h - 22*cm)

    section_title(h - 23.2*cm, "Employee Acknowledgment")
    pdf.setFont("Helvetica", 9)
    txt = pdf.beginText(2*cm, h - 24*cm)
    for line in ["I acknowledge receiving the above IT asset(s) in good working condition.",
                 "I agree to safeguard the equipment, use it only for work purposes,",
                 "and return it upon request or when leaving the organization.",
                 "In case of loss, misuse, or damage due to negligence, I accept full responsibility."]:
        txt.textLine(line)
    pdf.drawText(txt)

    pdf.setFont("Helvetica", 11)
    pdf.drawString(2*cm, h-27*cm, "Employee Signature: ___________________________")
    pdf.drawString(2*cm, h-28*cm, "IT Department:       ___________________________")
    pdf.drawString(12*cm, h-27*cm, "Date: ______________")
    pdf.drawString(12*cm, h-28*cm, "Date: ______________")

    pdf.setFillColorRGB(0.08, 0.22, 0.42)
    pdf.rect(0, 0, w, 1.2*cm, fill=True, stroke=False)
    pdf.setFillColorRGB(1,1,1)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(2*cm, 0.4*cm, "EtonHouse International School — IT Department — Confidential")

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f"handover_{record_id}.pdf",
                     mimetype="application/pdf")


# ─────────────────────────────────────────────
# HOLIDAY ASSET RETURN TRACKER
# ─────────────────────────────────────────────

# Staff email lookup — name as stored in assigned_to → email
# Only staff on the approved list; anyone not here will show "No email"
STAFF_EMAIL_MAP = {
    # ── K12 ──
    "Teresa Lambrechts":             "Teresa.Lambrechts@etonhouse.edu.sa",
    "Daniya Natha":                  "daniya.natha@etonhouse.edu.sa",
    "Yunjie Sun":                    "yunjie.sun@etonhouse.edu.sa",
    "Moncef Abdellawi":              "moncef.abdellawi@etonhouse.edu.sa",
    "Yasmeen Begum":                 "yasmeen.begum@etonhouse.edu.sa",
    "Rosol Moqbel":                  "rosol.moqbel@etonhouse.edu.sa",
    "Amina Reguiti":                 "amina.reguiti@etonhouse.edu.sa",
    "Simon Gilroy":                  "simon.gilroy@etonhouse.edu.sa",
    "Aya Areslan":                   "Aya.Areslan@etonhouse.edu.sa",
    "Nurse K12":                     "nurse.inter@etonhouse.com.sa",
    "Yasmin Mohamed":                "Yasmin.Mohamed@etonhouse.edu.sa",
    "Yasmin Mohamed (K12)":          "Yasmin.Mohamed@etonhouse.edu.sa",
    "Hanan AlMusaily":               "Hanan.AlMusaily@etonhouse.edu.sa",
    "Ayesha Gilroy":                 "ayesha.gilroy@etonhouse.edu.sa",
    "Jacqueline Nahirney":           "Jacqueline.Nahirney@etonhouse.edu.sa",
    "Jacqueline Elizabeth Nahirney": "Jacqueline.Nahirney@etonhouse.edu.sa",
    "Safia Hersi":                   "Safia.Hersi@etonhouse.edu.sa",
    "Amira Elgharib":                "Amira.Elgharib@etonhouse.edu.sa",
    # ── Preschool ──
    "Natasha Veronika":              "Natasha.Veronika@etonhouse.edu.sa",
    "Natasha":                       "Natasha.Veronika@etonhouse.edu.sa",
    "Atheer Al Anzan":               "Atheer.AlAnzan@etonhouse.edu.sa",
    "Aisha Mirza":                   "Aisha.Mirza@etonhouse.edu.sa",
    "Yasmin Rashid":                 "Yasmin.Rashid@etonhouse.edu.sa",
    "Yasmin Rashid (Pre-School)":    "Yasmin.Rashid@etonhouse.edu.sa",
    "Elanie VanDerNest":             "Elanie@etonhouse.edu.sa",
    "Elanie":                        "Elanie@etonhouse.edu.sa",
    "Naziha Mardam Bik":             "Naziha.MardamBik@etonhouse.com.sa",
    "Naziha Mardam":                 "Naziha.MardamBik@etonhouse.com.sa",
    "Halima Khanom":                 "Halima.Khanom@etonhouse.edu.sa",
    "Rachel Shadlock":               "Rachel.Shadlock@etonhouse.edu.sa",
    "Abir Al Mashjary":              "Abir.AlMashjary@etonhouse.edu.sa",
    "Hiba Shaarani":                 "Hiba.Shaarani@etonhouse.edu.sa",
    "Huda Jmaian":                   "Huda.Jmaian@etonhouse.edu.sa",
    "Preschool Nurse":               "nurse.preschool@etonhouse.edu.sa",
    "Hodo Ali":                      "Hodo.Ali@etonhouse.edu.sa",
    "Gaelin Kate Brown-Martin":      "Gaelin.Brown@etonhouse.edu.sa",
    "Hollie Tickle":                 "Hollie@etonhouse.edu.sa",
    "Hollie":                        "Hollie@etonhouse.edu.sa",
}

# Campus → CC recipients for exemption emails
CAMPUS_CC = {
    "EISG":  ["Vildana.Dupanovic@etonhouse.com.sa", "Marwen.khalifa@etonhouse.com.sa"],
    "EIPSG": ["elizabeth.cscahill@etonhouse.edu.sa",  "Marwen.khalifa@etonhouse.com.sa"],
    "HQ":    ["Marwen.khalifa@etonhouse.com.sa"],
    "EIEA":  ["Marwen.khalifa@etonhouse.com.sa"],
}

# Campus → display label for "Approved By" field
CAMPUS_APPROVERS = {
    "EISG":  "Vildana Dupanovic — K12 Principal / Marwen Khalifa — IT Manager",
    "EIPSG": "Elizabeth Connor-Scahill — Preschool Principal / Marwen Khalifa — IT Manager",
    "HQ":    "Marwen Khalifa — IT Manager",
    "EIEA":  "Marwen Khalifa — IT Manager",
}

IT_MANAGER_EMAIL = "Marwen.khalifa@etonhouse.com.sa"

# Staff excluded from the holiday tracker entirely
EXCLUDED_STAFF = {
    "Huda Alamari",
    "Vildana Dupanovic",      # K12 Principal — she is CC, not a tracked staff
    "Connor-Scahill Elizabeth Denise",
    "Elizabeth Connor",
    "Sadia Sidd",
    "Meshal Al Otaibi",
    "Sahar Alsabbagh",
}


@app.route("/holiday")
@login_required
def holiday():
    holiday_label = request.args.get("label", "Summer 2026")

    assigned = query("""
        SELECT a.*, h.id as hr_id, h.status as hr_status,
               h.staff_email, h.reason, h.returned_date, h.notes as hr_notes,
               h.approved_by
        FROM assets a
        LEFT JOIN holiday_returns h
            ON h.asset_id = a.id AND h.holiday_label = :label
        WHERE a.status = 'Assigned' AND a.assigned_to IS NOT NULL AND a.assigned_to != ''
        ORDER BY a.campus, a.asset_type, a.assigned_to
    """, {"label": holiday_label})

    # Filter out excluded staff and only show iPad/Laptop
    assigned = [
        r for r in assigned
        if r["assigned_to"] not in EXCLUDED_STAFF
        and r["asset_type"] in ("iPad", "Laptop")
    ]

    # Enrich each row with auto-looked-up email and campus approver
    for r in assigned:
        if not r["staff_email"]:
            r["staff_email"] = STAFF_EMAIL_MAP.get(r["assigned_to"], "")
        r["campus_approver"] = CAMPUS_APPROVERS.get(r["campus"], CAMPUS_APPROVERS["HQ"])

    total    = len(assigned)
    pending  = sum(1 for r in assigned if not r["hr_status"] or r["hr_status"] == "pending")
    exempt   = sum(1 for r in assigned if r["hr_status"] == "exempt")
    returned = sum(1 for r in assigned if r["hr_status"] == "returned")

    return render_template("holiday.html",
        assets=assigned, holiday_label=holiday_label,
        total=total, pending=pending, exempt=exempt, returned=returned,
        campuses=CAMPUSES,
        staff_email_map=STAFF_EMAIL_MAP,
        campus_approvers=CAMPUS_APPROVERS,
        it_manager_email=IT_MANAGER_EMAIL)


@app.route("/holiday/update/<int:asset_id>", methods=["POST"])
@login_required
def holiday_update(asset_id):
    try:
        holiday_label = request.form.get("holiday_label", "Summer 2026")
        status        = request.form.get("status", "pending")
        staff_email   = request.form.get("staff_email", "").strip()
        reason        = request.form.get("reason", "").strip()
        notes         = request.form.get("notes", "").strip()
        returned_date = request.form.get("returned_date", "")
        approved_by   = request.form.get("approved_by", "").strip() or IT_MANAGER_EMAIL

        rows = query("SELECT * FROM assets WHERE id=:id", {"id": asset_id})
        if not rows:
            flash("Asset not found.", "danger")
            return redirect(url_for("holiday"))
        asset = rows[0]

        # Auto-lookup email if not supplied
        if not staff_email:
            staff_email = STAFF_EMAIL_MAP.get(asset["assigned_to"], "")

        existing = query(
            "SELECT id FROM holiday_returns WHERE asset_id=:aid AND holiday_label=:label",
            {"aid": asset_id, "label": holiday_label}
        )
        if existing:
            execute("""
                UPDATE holiday_returns
                SET status=:st, staff_email=:em, reason=:re, notes=:nt,
                    returned_date=:rd, approved_by=:ab
                WHERE asset_id=:aid AND holiday_label=:label
            """, dict(st=status, em=staff_email, re=reason, nt=notes,
                      rd=returned_date, ab=approved_by,
                      aid=asset_id, label=holiday_label))
        else:
            execute("""
                INSERT INTO holiday_returns
                    (asset_id, staff_name, staff_email, campus, holiday_label,
                     status, reason, approved_by, returned_date, notes)
                VALUES (:aid, :sn, :em, :ca, :lb, :st, :re, :ab, :rd, :nt)
            """, dict(aid=asset_id, sn=asset["assigned_to"], em=staff_email,
                      ca=asset["campus"], lb=holiday_label, st=status,
                      re=reason, ab=approved_by, rd=returned_date, nt=notes))

    except Exception as db_err:
        print("DB error in holiday_update:", db_err)
        flash(f"Database error: {db_err}", "danger")
        return redirect(url_for("holiday"))

    # Send confirmation email to staff (only when marking Exempt)
    if status == "exempt" and staff_email:
        mail_configured = bool(app.config.get("MAIL_SERVER"))
        if not mail_configured:
            flash(
                f"Status saved as Exempt for {asset['assigned_to']}. "
                f"⚠️ Email NOT sent — SMTP not configured on Render. "
                f"Add MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD env vars.",
                "warning"
            )
        else:
            try:
                first_name = asset["assigned_to"].split()[0]
                cc_list = CAMPUS_CC.get(asset["campus"], [IT_MANAGER_EMAIL])
                body = (
                    f"Hi {first_name},\n\n"
                    f"This is an automated email from your IT Department.\n\n"
                    f"Please confirm whether you will keep your IT asset(s) with you "
                    f"during the Holiday vacation or not:\n\n"
                    f"  Asset Type : {asset['asset_type']}\n"
                    f"  Serial No. : {asset['serial_number'] or 'N/A'}\n"
                    f"  Model      : {asset.get('model_name') or 'N/A'}\n\n"
                    f"If YES — please reply to this email with the Serial Number of "
                    f"each asset you have with you.\n\n"
                    f"If NO — please return the device to the IT Office before your "
                    f"last working day (6th July 2026).\n\n"
                    f"Best Regards,\n"
                    f"Marwen\n"
                    f"IT Department — EtonHouse International School, Riyadh"
                )
                mail.send(Message(
                    subject=f"[IT] Asset Confirmation Required — {holiday_label} Holiday",
                    sender=app.config.get("MAIL_DEFAULT_SENDER", IT_MANAGER_EMAIL),
                    recipients=[staff_email],
                    cc=cc_list,
                    body=body
                ))
                flash(f"✅ Confirmation email sent to {staff_email}.", "success")
            except Exception as mail_err:
                import traceback as tb
                err_detail = tb.format_exc()
                print("Email error:", err_detail)
                flash(f"Status saved as Exempt. Email failed — {type(mail_err).__name__}: {mail_err}", "warning")
    elif status == "returned":
        flash("Asset marked as returned.", "success")
    else:
        flash("Status updated.", "success")

    return redirect(url_for("holiday", label=holiday_label))


@app.route("/holiday/debug")
@login_required
def holiday_debug():
    import traceback
    results = []
    # Test 1: DB connection
    try:
        count = scalar("SELECT COUNT(*) FROM holiday_returns")
        results.append(f"✅ holiday_returns table OK — {count} rows")
    except Exception as e:
        results.append(f"❌ holiday_returns table ERROR: {e}")

    # Test 2: approved_by column
    try:
        query("SELECT approved_by FROM holiday_returns LIMIT 1")
        results.append("✅ approved_by column exists")
    except Exception as e:
        results.append(f"❌ approved_by column MISSING: {e}")

    # Test 3: mail config
    mail_server = app.config.get("MAIL_SERVER")
    mail_user   = app.config.get("MAIL_USERNAME")
    results.append(f"📧 MAIL_SERVER = {mail_server!r}")
    results.append(f"📧 MAIL_USERNAME = {mail_user!r}")

    # Test 4: test INSERT
    try:
        execute("""
            INSERT INTO holiday_returns
                (asset_id, staff_name, staff_email, campus, holiday_label,
                 status, reason, approved_by, returned_date, notes)
            VALUES (:aid, :sn, :em, :ca, :lb, :st, :re, :ab, :rd, :nt)
        """, dict(aid=99999, sn='TEST', em='test@test.com', ca='EIPSG',
                  lb='DEBUG', st='pending', re='', ab='', rd='', nt=''))
        execute("DELETE FROM holiday_returns WHERE asset_id=99999 AND holiday_label='DEBUG'",{})
        results.append("✅ INSERT/DELETE test OK")
    except Exception as e:
        results.append(f"❌ INSERT test ERROR: {traceback.format_exc()}")

    return "<br>".join(results) + "<br><br><a href='/holiday'>Back</a>"


@app.route("/holiday/send-reminder", methods=["POST"])
@login_required
def holiday_send_reminder():
    holiday_label = request.form.get("holiday_label", "Summer 2025")
    deadline      = request.form.get("deadline", "Friday, 4th July")

    # Get all pending assigned assets
    pending = query("""
        SELECT a.*, h.status as hr_status
        FROM assets a
        LEFT JOIN holiday_returns h
            ON h.asset_id = a.id AND h.holiday_label = :label
        WHERE a.status = 'Assigned'
          AND a.assigned_to IS NOT NULL AND a.assigned_to != ''
          AND (h.status IS NULL OR h.status = 'pending')
    """, {"label": holiday_label})

    sent = 0
    for asset in pending:
        # Try to find email from handover records
        hr = query(
            "SELECT * FROM handover WHERE serial=:sn ORDER BY id DESC LIMIT 1",
            {"sn": asset["serial_number"]}
        )
        recipient = os.environ.get("MAIL_DEFAULT_SENDER", "marwen.khalifa@etonhouse.com.sa")
        try:
            body = (
                f"Dear {asset['assigned_to']},\n\n"
                f"This is a reminder to return the following IT asset to the IT Office "
                f"by {deadline}:\n\n"
                f"  Asset Type : {asset['asset_type']}\n"
                f"  Serial No. : {asset['serial_number']}\n"
                f"  Model      : {asset.get('model_name','')}\n\n"
                f"If you require this device during the holiday period for work purposes, "
                f"please contact the IT Department immediately to request an exemption.\n\n"
                f"Best regards,\n{current_user.id.capitalize()}\nEtonHouse IT Department"
            )
            mail.send(Message(
                subject=f"Reminder: IT Asset Return by {deadline} — EtonHouse",
                sender=os.environ.get("MAIL_DEFAULT_SENDER", "it@etonhouse.com.sa"),
                recipients=[recipient],
                body=body
            ))
            sent += 1
        except Exception as e:
            print("Reminder email error:", e)

    flash(f"Reminder sent for {sent} pending asset(s).", "success")
    return redirect(url_for("holiday", label=holiday_label))


@app.errorhandler(500)
def internal_error(e):
    import traceback
    return (
        f"<h2 style='font-family:monospace;color:#c53030'>500 — Internal Server Error</h2>"
        f"<pre style='background:#1a1a1a;color:#f87171;padding:20px;font-size:13px;"
        f"border-radius:8px;overflow:auto'>{traceback.format_exc()}</pre>"
        f"<p><a href='/holiday'>← Back to Holiday Tracker</a></p>"
    ), 500


if __name__ == "__main__":
    app.run(debug=True)
