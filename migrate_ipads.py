"""
One-time migration script: upsert iPad inventory from spreadsheet.
Run on Render shell: python migrate_ipads.py
Does NOT delete any existing records.
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///database.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,
)

# (serial, part_number, assigned_to, campus, status, remarks)
# Rows 3,7,17,18 struck through red → Lost/Stolen
# Row 21 → IT Store (In Store)
IPADS = [
    ("SD99WMJ9W39", "MD4G4AB/A", "Hanan Almusaily",    "EISG",  "Assigned",    ""),
    ("SFWHCWC123L", "MD4G4AB/A", "Hollie Tickle",       "EISG",  "Assigned",    ""),
    ("SJXJLYP2WNN", "MD4G4AB/A", "Chelsea Jones",       "EISG",  "Lost/Stolen", "Teacher left without turning it back"),
    ("SK21QYGQPFX", "MD4G4AB/A", "Fardousa Hassan",     "EISG",  "Assigned",    ""),
    ("SKG5LXN10VM", "MD4G4AB/A", "Ayesha Gilroy",       "EISG",  "Assigned",    ""),
    ("SKR934Y34DK", "MD4G4AB/A", "Karina Smith",        "EISG",  "Assigned",    ""),
    ("SL3369CC42Y", "MD4G4AB/A", "Yunjie Sun",          "EISG",  "Lost/Stolen", "Theft from school"),
    ("SFQVDXW1610", "MD4G4AB/A", "Mildred Ijedinma",    "EISG",  "Assigned",    ""),
    ("SH6PYPYD4VD", "MD4G4AB/A", "Samantha Coble",      "EISG",  "Assigned",    ""),
    ("SCXLG9GY045", "MD4G4AB/A", "Alexus Bailey",       "EISG",  "Assigned",    ""),
    ("SDJWR29FY9C", "MD4G4AB/A", "Natasha Veronika",    "EIPSG", "Assigned",    ""),
    ("SG909J07Q4K", "MD4G4AB/A", "Teresa Lambrechts",   "EISG",  "Assigned",    ""),
    ("SH2TV6XG2QY", "MD4G4AB/A", "Yasmin Rashid",       "EIPSG", "Assigned",    ""),
    ("SJ23T775144", "MD4G4AB/A", "Elanie Van Der Nest", "EIPSG", "Assigned",    ""),
    ("SJY71XCGWJR", "MD4G4AB/A", "Aisha Mirza",         "EIPSG", "Assigned",    ""),
    ("SK23WT3J9KY", "MD4G4AB/A", "Halima Khanom",       "EIPSG", "Assigned",    ""),
    ("SLM7J2GJY7C", "MD4G4AB/A", "Twane Coaker",        "EISG",  "Lost/Stolen", "Teacher left without turning it back"),
    ("SXX73VNXT9P", "MD4G4AB/A", "Daniya Natha",        "EISG",  "Lost/Stolen", "Theft from school"),
    ("CFQ4H60C6K",  "MD4H4AB/A", "Hodo Ali",            "EIPSG", "Assigned",    ""),
    ("D3N9R2KR45",  "MD4H4AB/A", "Jacqueline Nahirney", "EISG",  "Assigned",    ""),
    ("MK2LYYCWY3",  "MD4H4AB/A", "IT Store",            "EISG",  "In Store",    ""),
    ("D76G9Q03CR",  "MD4H4AB/A", "Gaelin Brown",        "EIPSG", "Assigned",    ""),
]

MODEL = "iPad WiFi 256GB SLV-SAU"

inserted = 0
updated = 0

with engine.connect() as conn:
    for serial, part, assigned_to, campus, status, remarks in IPADS:
        existing = conn.execute(
            text("SELECT id FROM assets WHERE serial_number = :s"),
            {"s": serial}
        ).fetchone()

        if existing:
            conn.execute(text("""
                UPDATE assets
                SET assigned_to  = :assigned_to,
                    campus       = :campus,
                    status       = :status,
                    remarks      = :remarks,
                    model_name   = :model,
                    part_number  = :part,
                    asset_type   = 'iPad'
                WHERE serial_number = :s
            """), {"assigned_to": assigned_to, "campus": campus, "status": status,
                   "remarks": remarks, "model": MODEL, "part": part, "s": serial})
            print(f"  UPDATED  {serial} → {assigned_to} ({status})")
            updated += 1
        else:
            conn.execute(text("""
                INSERT INTO assets (asset_type, serial_number, part_number, model_name,
                                    assigned_to, campus, status, remarks)
                VALUES ('iPad', :s, :part, :model, :assigned_to, :campus, :status, :remarks)
            """), {"s": serial, "part": part, "model": MODEL, "assigned_to": assigned_to,
                   "campus": campus, "status": status, "remarks": remarks})
            print(f"  INSERTED {serial} → {assigned_to} ({status})")
            inserted += 1

    conn.commit()

print(f"\nDone: {inserted} inserted, {updated} updated. No records deleted.")
