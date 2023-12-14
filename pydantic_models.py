# pydantic_models.py

from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    price: int


class ProcessPurchase(BaseModel):
    amount: int


class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True
