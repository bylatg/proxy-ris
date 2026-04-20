from sqlalchemy import select

from app.db import SessionLocal
from app.models.user import User
from app.security import hash_password


def main():
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.username == "admin"))
        if existing:
            print("Admin already exists")
            return

        user = User(
            email="admin@example.com",
            username="admin",
            password_hash=hash_password("123ad"),
            is_admin=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print("Admin created: admin / admin123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
