# debug_data.py
from sqlalchemy import create_engine, text
from datetime import date
import os

# Use your exact DB connection string from main.py
DATABASE_URL = "postgresql://your_username:your_password@localhost/leadmatrix_db"  # Replace with yours
engine = create_engine(DATABASE_URL)

business_id = 71
start_date = '2026-03-02'
end_date = '2026-04-01'

print("=== RAW GMBInsight DATA ===\n")

# Raw data from DB
query = text("""
    SELECT date, 
           phone_calls, directions, website_clicks,
           conversations, bookings,
           phone_calls + COALESCE(directions, 0) + COALESCE(website_clicks, 0) as daily_total
    FROM gmb_insights 
    WHERE business_id = :business_id 
      AND date >= :start_date 
      AND date <= :end_date
    ORDER BY date;
""")

with engine.connect() as conn:
    result = conn.execute(query, {
        "business_id": business_id,
        "start_date": start_date,
        "end_date": end_date
    }).fetchall()
    
    total_calls = 0
    total_dirs = 0
    total_daily = 0
    
    for row in result:
        print(f"{row.date}: calls={row.phone_calls}, dirs={row.directions}, total={row.daily_total}")
        total_calls += row.phone_calls or 0
        total_dirs += row.directions or 0
        total_daily += row.daily_total or 0
    
    print(f"\n=== TOTALS ===")
    print(f"DB Calls sum: {total_calls}")
    print(f"DB Directions sum: {total_dirs}")
    print(f"DB Daily totals sum: {total_daily}")
    print(f"API reported: 85")
    print(f"Discrepancy: {total_daily - 85}")

print("\n=== MODEL COLUMNS ===")
# Check what columns actually exist
with engine.connect() as conn:
    columns = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'gmb_insights' 
          AND column_name LIKE '%call%' OR column_name LIKE '%direct%' OR column_name LIKE '%inter%'
        ORDER BY column_name;
    """)).fetchall()
    
    for col in columns:
        print(f"{col.column_name}: {col.data_type}")