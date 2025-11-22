import os
import pymysql
from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine, text

# Cloud SQL info from environment variables
INSTANCE_CONNECTION = os.environ.get("INSTANCE_CONNECTION")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")

# Create connector
connector = Connector()

def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

# Create SQLAlchemy engine
engine = create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

