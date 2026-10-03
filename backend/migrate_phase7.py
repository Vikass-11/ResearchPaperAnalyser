
from app.models.database import engine
from app.models.schema import Base
print("Creating new tables...")
Base.metadata.create_all(bind=engine)
print("Done.")

