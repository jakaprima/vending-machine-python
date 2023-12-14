from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost/db_vending_machine"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Integer)
