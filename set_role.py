import sys

from database import SessionLocal
from models import User


VALID_ROLES = {
    "employee",
    "manager",
    "it_head"
}


def main():

    if len(sys.argv) != 3:
        print(
            "Usage: python set_role.py "
            "EMAIL employee|manager|it_head"
        )
        raise SystemExit(1)

    email = sys.argv[1].strip()
    role = sys.argv[2].strip().lower()

    if role not in VALID_ROLES:
        print(
            "Invalid role. Choose one of: "
            + ", ".join(sorted(VALID_ROLES))
        )
        raise SystemExit(1)

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.email == email
        ).first()

        if user is None:
            print("User not found. Sign up first.")
            raise SystemExit(1)

        user.role = role
        db.commit()

        print(
            f"Updated {email} role to {role}."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()