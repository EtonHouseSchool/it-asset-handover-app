"""
One-time migration script: upsert iPad inventory from spreadsheet.
Run locally or on Render via: python migrate_ipads.py
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

# iPad inventory from spreadsheet.
# status: "Lost/Stolen" for struck-through red rows, else "Assigned"
IPADS = [
    # serial,          assigned_to,             campus,   status,         remarks
    ("DMPFQ6YGPM",  "Hanan Almusaily",       "EISG",   "Assigned",     ""),
    ("DMPFQ6M8PM",  "Chelsea Jones",         "EISG",   "Lost/Stolen",  "Lost"),
    ("DMPFQF7NPM",  "Hollie Tickle",         "EISG",   "Assigned",     ""),
    ("DMPFQ6LHPM",  "Fardousa Hassan",       "EISG",   "Assigned",     ""),
    ("DMPFQ6NTPM",  "Ayesha Gilroy",         "EISG",   "Assigned",     ""),
    ("DMPFQ6MYPM",  "Karina Smith",          "EISG",   "Assigned",     ""),
    ("DMPFQ6MPPM",  "Yunjie Sun",            "EISG",   "Lost/Stolen",  "Theft"),
    ("DMPFQ6MMPM",  "Mildred Ijedinma",      "EISG",   "Assigned",     ""),
    ("DMPFQ6MNPM",  "Samantha Coble",        "EISG",   "Assigned",     ""),
    ("DMPFQ6MQPM",  "Alexus Bailey",         "EISG",   "Assigned",     ""),
    ("DMPFQ6MTPM",  "Natasha Veronika",      "EISG",   "Assigned",     ""),
    ("DMPFQ6M7PM",  "Teresa Lambrechts",     "EISG",   "Assigned",     ""),
    ("DMPFQ6MWPM",  "Yasmin Rashid",         "EISG",   "Assigned",     ""),
    ("DMPFQF76PM",  "Elanie Van Der Nest",   "EISG",   "Assigned",     ""),
    ("DMPFQ6MXPM",  "Aisha Mirza",           "EISG",   "Assigned",     ""),
    ("DMPFQ6MVPM",  "Halima Khanom",         "EIPSG",  "Assigned",     ""),
    ("DMPFQ6M2PM",  "Twane Cooker",          "EIPSG",  "Lost/Stolen",  "Left school"),
    ("DMPFQ6M3PM",  "Daniya Natha",          "EIPSG",  "Lost/Stolen",  "Theft"),
    ("DMPFQ6M4PM",  "Hodo Ali",              "EIPSG",  "Assigned",     ""),
    ("DMPFQ6M5PM",  "Jacqueline Nahirney",   "EIPSG",  "Assigned",     ""),
    ("DMPFQ6M6PM",  "Gaelin Brown",          "EIPSG",  "Assigned",     ""),
]

MODEL = "iPad WIFI 256GB SLV-SAU"

inserted = 0
updated = 0

with engine.connect() as conn:
    for serial, assigned_to, campus, status, remarks in IPADS:
        existing = conn.execute(
            text("SELECT id FROM assets WHERE serial_number = :s"),
            {"s": serial}
        ).fetchone()

        if existing:
            conn.execute(text("""
                UPDATE assets
                SET assigned_to = :assigned_to,
                    campus      = :campus,
                    status      = :status,
                    remarks     = :remarks,
                    model_name  = :model,
                    asset_type  = 'iPad'
                WHERE serial_number = :s
            """), {"assigned_to": assigned_to, "campus": campus, "status": status,
                   "remarks": remarks, "model": MODEL, "s": serial})
            print(f"  UPDATED  {serial} → {assigned_to} ({status})")
            updated += 1
        else:
            conn.execute(text("""
                INSERT INTO assets (asset_type, serial_number, model_name, assigned_to, campus, status, remarks)
                VALUES ('iPad', :s, :model, :assigned_to, :campus, :status, :remarks)
            """), {"s": serial, "model": MODEL, "assigned_to": assigned_to,
                   "campus": campus, "status": status, "remarks": remarks})
            print(f"  INSERTED {serial} → {assigned_to} ({status})")
            inserted += 1

    conn.commit()

print(f"\nDone: {inserted} inserted, {updated} updated. No records deleted.")
