"""
Database initialization script
Run this once to create all tables
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, check_db_connection
from app.models import (
    Business, ApiKey, BusinessMetric, CompetitorAnalysis,
    CompetitorTracking, Review, GMBPost, User, Notification,
    AuditLog, Webhook, ScheduledTask
)

def main():
    print("=" * 60)
    print("GMB Dashboard - Database Initialization")
    print("=" * 60)
    
    # Check connection
    print("\n1. Checking database connection...")
    if not check_db_connection():
        print("❌ Cannot connect to database. Please check your .env file.")
        return
    
    # Create tables
    print("\n2. Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # List created tables
        print("\n3. Created tables:")
        tables = [
            "businesses", "api_keys", "users", "business_metrics",
            "competitor_analysis", "competitor_tracking", "reviews",
            "gmb_posts", "notifications", "audit_logs", "webhooks",
            "scheduled_tasks"
        ]
        for table in tables:
            print(f"   ✓ {table}")
        
        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)
        print("\nYou can now run: uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()