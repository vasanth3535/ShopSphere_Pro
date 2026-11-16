from getpass import getpass
from sqlalchemy import select, or_

from database.connection import SessionLocal
from models.user import User
from utils.security import hash_password

db = SessionLocal()

try:
    if db.scalar(select(User).where(User.role == "SUPER_ADMIN")):
        print("SUPER_ADMIN already exists.")
    else:
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        email = input("Email: ").strip().lower()
        phone = input("Phone: ").strip()
        password = getpass("Password: ")
        confirm = getpass("Confirm password: ")

        if not all([first_name, last_name, email, phone, password]):
            raise ValueError("All fields are required.")

        if password != confirm or len(password) < 8:
            raise ValueError("Passwords must match and contain at least 8 characters.")

        duplicate = db.scalar(
            select(User).where(
                or_(User.email == email, User.phone == phone)
            )
        )

        if duplicate:
            raise ValueError("Email or phone already exists.")

        admin = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            role="SUPER_ADMIN",
            is_active=True,
            is_email_verified=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("SUPER_ADMIN created successfully. ID:", admin.id)

except Exception as error:
    db.rollback()
    print("Error:", error)
finally:
    db.close()
