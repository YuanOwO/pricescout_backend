from __future__ import annotations

import json
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import Product, create_session

app = FastAPI(root_path="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HelloWorld(BaseModel):
    message: str = "Hello World"


class Category(BaseModel):
    name: str
    children: List[Category] = []


class ProductModel(BaseModel):
    pid: int
    pno: Optional[str]
    barcode: Optional[str]
    name: str
    price: int
    spec: float
    unit: str
    price_unit: float
    channel: str
    category1: str
    category2: str
    category3: str
    url: str
    pic_url: str


class ProductResponse(BaseModel):
    total_count: int
    page: int
    limit: int
    products: List[ProductModel]


@app.get("/", summary="Hello World", response_model=HelloWorld)
async def root():
    """
    測試 API 是否正常運作
    """
    return {"message": "Hello World"}


@app.get("/category", summary="所有商品分類")
async def category():
    """
    取得所有商品分類
    """
    with open("data/categories.json", "r", encoding="utf-8") as f:
        cats = json.load(f)

    return cats


@app.get("/subcategory", summary="取得該商品分類的子分類", response_model=List[str])
async def subcategory(
    category1: Optional[str] = Query(None, description="指定商品的第一層分類"),
    category2: Optional[str] = Query(None, description="指定商品的第二層分類"),
    category3: Optional[str] = Query(None, description="指定商品的第三層分類"),
):
    """
    取得該商品分類的子分類
    """

    with open("data/categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    cats = {}

    for cat in categories["category"]:
        cat1 = cat["name"]
        cats[cat1] = {}
        for cat in cat["children"]:
            cat2 = cat["name"]
            cats[cat1][cat2] = {}
            if "children" in cat:
                for cat in cat["children"]:
                    cat3 = cat["name"]
                    cats[cat1][cat2][cat3] = {}

    try:
        if category3:
            ret = cats[category1][category2][category3].keys()
        elif category2:
            ret = cats[category1][category2].keys()
        elif category1:
            ret = cats[category1].keys()
        else:
            ret = cats.keys()
    except KeyError:
        ret = []

    return list(ret)


@app.get("/channels", summary="所有通路商", response_model=List[str])
async def channels():
    """
    取得所有通路商
    """

    return ["全聯", "家樂福"]


@app.get("/products", tags=["產品"], summary="取得商品列表", response_model=ProductResponse)
async def products(
    category1: Optional[str] = Query(None, description="指定商品的第一層分類"),
    category2: Optional[str] = Query(None, description="指定商品的第二層分類"),
    category3: Optional[str] = Query(None, description="指定商品的第三層分類"),
    channel: Optional[str] = Query(None, description="指定商品的通路商"),
    query: Optional[str] = Query(None, description="查詢商品名稱"),
    page: Optional[int] = Query(1, ge=1, description="查詢第幾頁"),
    limit: Optional[int] = Query(10, ge=1, description="每頁顯示幾筆資料"),
):
    """
    取得商品列表
    """
    # print(category1, category2, category3, page, limit)

    session = create_session()
    products = session.query(Product)

    if category1:
        products = products.filter(Product.category1 == category1)
    if category2:
        products = products.filter(Product.category2 == category2)
    if category3:
        products = products.filter(Product.category3 == category3)
    if channel:
        products = products.filter(Product.channel == channel)
    if query:
        products = products.filter(Product.name.contains(query))

    total_count = products.count()
    products = products.order_by(Product.price_unit.asc())
    products = products.offset((page - 1) * limit).limit(limit)

    return {
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "products": products.all(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)
