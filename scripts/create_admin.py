from sqlalchemy import select

from app.db import SessionLocal
from app.models.user import User
from app.security import hash_password


def main():
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.username == "Dimas"))
        if existing:
            print("User already exists")
            return

        user = User(
            email="dimas@example.com",
            username="Dimas",
            password_hash=hash_password("@maybachov"),
            is_admin=False,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print("User created: admin / admin123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
