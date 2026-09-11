from app.db import SessionLocal, init_db
from app.services.seed import seed_demo_data


if __name__ == "__main__":
    init_db()
    with SessionLocal() as db:
        seed_demo_data(db)
    print("Synthetic emergency-response demo data seeded.")
