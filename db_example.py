from sqlalchemy import create_engine
from sqlalchemy.engine import URL

url = URL.create(
    "postgresql+psycopg2",
    username="postgres",
    password="YOUR_PASSWORD",
    host="localhost",
    port=5432,
    database="olist_db",
)

engine = create_engine(url)
