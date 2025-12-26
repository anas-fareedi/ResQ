from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
from dotenv import load_dotenv
import os

load_dotenv()  

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
       

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
