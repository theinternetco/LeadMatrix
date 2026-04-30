"""
One-time script to create team accounts.
Run from the project root:  python seed_users.py

Edit the USERS list below before running.
Passwords should be changed after first login (no self-service reset yet).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User
from app.routers.auth import hash_password

USERS = [
    {"email": "zishan@theinternetcompany.in",  "full_name": "Zishan",  "password": "changeme123"},
    {"email": "abhishek@theinternetcompany.in",  "full_name": "Abhishek",  "password": "changeme123"},
    {"email": "arbaz@theinternetcompany.in",  "full_name": "Arbaz",  "password": "changeme123"},
    {"email": "himanshu@theinternetcompany.in",  "full_name": "Himanshu",  "password": "changeme123"},
    {"email": "shailesh@theinternetcompany.in",  "full_name": "Shailesh",  "password": "changeme123"},
    # Add more team members:
    # {"email": "name@theinternetcompany.in", "full_name": "Name", "password": "changeme123"},
]

def main():
    db = SessionLocal()
    try:
        for u in USERS:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
                print(f"⚠️  {u['email']} already exists — skipping")
                continue
            user = User(
                email           = u["email"],
                full_name       = u["full_name"],
                hashed_password = hash_password(u["password"]),
                is_active       = True,
                is_verified     = True,
            )
            db.add(user)
            db.commit()
            print(f"✅ Created {u['email']}  (password: {u['password']})")
    finally:
        db.close()
    print("\nDone. Share credentials with your team and ask them to change passwords.")

if __name__ == "__main__":
    main()
