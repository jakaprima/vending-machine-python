import json

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session

from pydantic_models import Product as ProductPydantic, ProductBase, ProcessPurchase
from models import Product, Base
from typing import List
import redis
import uuid
from config.db import get_db

app = FastAPI()
r = redis.Redis(host='localhost', port=6379, db=0)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Vending Machine API",
        version="1.0.0",
        description="API for managing products in a vending machine",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


def find_combination(total_amount: int):
    combinations = []
    # Check all combinations of denominations
    for num_2000 in range(total_amount // 2000 + 1):
        print("num 2000", num_2000)
        for num_5000 in range(total_amount // 5000 + 1):
            print("num 5000", num_5000)
            if (num_2000 * 2000 + num_5000 * 5000) == total_amount:
                combinations.append((num_2000, num_5000))
    return combinations


@app.post("/products/", response_model=ProductPydantic, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductBase, db: Session = Depends(get_db)):
    # Handling the case where the price is not an accepted denomination
    # Find a combination of 2000 and 5000 denominations and accept 7000, 9000, 12000
    combinations = find_combination(product.price)
    if not combinations:
        raise HTTPException(status_code=400,
                            detail="The rule is that the vending machine can only accept "
                                   "denominations Rp. 5000 and Rp. 2000.")
    else:
        # Check if the product name already exists
        existing_product = db.query(Product).filter(Product.name == product.name).first()
        if existing_product:
            raise HTTPException(status_code=400, detail="Product with this name already exists.")
        db_product = Product(**product.dict())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product


@app.get("/products/{product_id}", response_model=ProductPydantic)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products/", response_model=List[ProductPydantic])
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products


@app.put("/products/{product_id}", response_model=ProductPydantic)
def update_product(product_id: int, product_update: ProductBase, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    combinations = find_combination(product_update.price)
    if not combinations:
        raise HTTPException(status_code=400,
                            detail="The rule is that the vending machine can "
                                   "only accept denominations Rp. 5000 and "
                                   "Rp. 2000.")
    else:
        for attr, value in product_update.dict(exclude_unset=True).items():
            setattr(db_product, attr, value)

        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product


@app.delete("/products/{product_id}", response_model=ProductPydantic)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(db_product)
    db.commit()
    return db_product


@app.post("/machine-process-money/")
async def machine_process_money(payload: ProcessPurchase, db: Session = Depends(get_db)):
    """
    get products available by inserted money
    :param payload: payload.amount
    :param db:
    :return: dict
    """
    generated_uuid = uuid.uuid4()

    # Convert the UUID to string if needed
    uuid_string = str(generated_uuid)
    if not r.get('machine_process'):
        amount = payload.amount
        combinations = find_combination(amount)
        productPurchaseAble = []
        if not combinations:
            raise HTTPException(status_code=400,
                                detail="only accept denominations Rp. 5000 and Rp. 2000.")
        else:
            products = db.query(Product).all()
            for product_instance in products:
                if product_instance.price <= amount:
                    product_data = {
                        "id": product_instance.id,
                        "name": product_instance.name,
                        "price": product_instance.price,
                    }
                    productPurchaseAble.append(product_data)

        r.set("machine_process",
              json.dumps({"process": uuid_string,
                          "amount": payload.amount,
                          "products": productPurchaseAble}))
        return {
            "process": uuid_string,
            "productPurchaseAble": productPurchaseAble
        }
    else:
        machine_process = json.loads(r.get('machine_process'))
        raise HTTPException(status_code=400,
                            detail={
                                "product_list": machine_process["products"],
                                "description": "machine still process money. select product to buy"
                            })


@app.get("/purchase/{process_id}/{selected_product_index}")
async def purchase(process_id: str, selected_product_index: int, db: Session = Depends(get_db)):
    if r.get("machine_process"):
        machine_process = json.loads(r.get('machine_process'))
        print("purchase", process_id)
        print("selected_product", selected_product_index)
        selected_product = machine_process["products"][selected_product_index]

        amount = machine_process["amount"]
        processing_amount = amount
        print("A", selected_product)
        print("AMOUNT", amount)
        quantity = 0
        while True:
            if processing_amount <= 0:
                break
            processing_amount = processing_amount - selected_product["price"]
            quantity = quantity + 1
        r.delete("machine_process")

        return {
            "selected_product_name": selected_product["name"],
            "amount": amount,
            "quantity": f"{quantity}",
            "output": f'{quantity} {selected_product["name"]}'
        }
    else:
        raise HTTPException(status_code=400,
                            detail="please insert money, use API /machine-process-money.")
