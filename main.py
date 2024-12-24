from __future__ import annotations

import json
from typing import List, Optional

import uvicorn
from fastapi import APIRouter, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from database import Product, create_session

app = FastAPI(
    title="PriceScout API",
    summary="超市商品比價網 後端資料庫 API",
    version="1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter()


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/index.html", media_type="text/html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon_ico():
    return FileResponse("static/favicon.ico", media_type="image/x-icon")


@app.get("/favicon.png", include_in_schema=False)
async def favicon_png():
    return FileResponse("static/favicon.png", media_type="image/png")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


########################################################################


class HelloWorld(BaseModel):
    message: str = "Hello World"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"message": "Hello World"},
            ]
        }
    }


@api.get("/", summary="Hello World (API 根目錄)", response_model=HelloWorld)
async def helloworld():
    """
    這個是 API 的根目錄
    用來測試 API 是否正常運作
    """
    return {"message": "Hello World"}


########################################################################


class Category(BaseModel):
    name: str
    children: Optional[List["Category"]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "生鮮", "children": [{"name": "蔬菜"}, {"name": "水果"}]},
                {"name": "油米雜糧"},
            ]
        }
    }


class CategoryResponse(BaseModel):
    category: List[Category]


@api.get("/category", tags=["商品分類"], summary="所有商品分類", response_model=CategoryResponse)
async def category():
    """
    取得所有商品分類
    """
    return FileResponse("data/categories.json", media_type="application/json")


@api.get("/subcategory", tags=["商品分類"], summary="取得商品子分類", response_model=List[str])
async def subcategory(
    category1: Optional[str] = Query(None, description="指定商品的第一層分類"),
    category2: Optional[str] = Query(None, description="指定商品的第二層分類"),
    category3: Optional[str] = Query(None, description="指定商品的第三層分類"),
):
    """
    根據指定的商品分類，回傳他的下一層子分類有哪些。
    若沒有指定分類，則回傳所有第一層分類。
    若找不到指定的分類，則回傳空陣列。
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

    ret = list(ret)

    return ret


########################################################################


class ChannelsResponse(BaseModel):
    channels: List[str]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"channels": ["全聯", "家樂福"]},
            ]
        }
    }


@api.get("/channels", tags=["通路商"], summary="取得所有通路商", response_model=ChannelsResponse)
async def channels():
    """
    取得所有通路商。
    不過目前只有全聯福利中心和家樂福。
    """

    return {"channels": ["全聯", "家樂福"]}


########################################################################


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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "pid": 1,
                    "pno": "123456",
                    "barcode": "1234567890123",
                    "name": "商品名稱",
                    "price": 100,
                    "spec": 100,
                    "unit": "g",
                    "price_unit": 1,
                    "channel": "全聯",
                    "category1": "生鮮",
                    "category2": "蔬菜",
                    "category3": "葉菜類",
                    "url": "https://www.example.com",
                    "pic_url": "https://www.example.com/pic.jpg",
                },
            ]
        }
    }


class ProductsResponse(BaseModel):
    total_count: int
    page: int = 1
    limit: int = 10
    products: List[ProductModel]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_count": 1,
                    "page": 1,
                    "limit": 10,
                    "products": [
                        {
                            "barcode": "1234567890123",
                            "category1": "生鮮",
                            "category2": "蔬菜",
                            "category3": "葉菜類",
                            "channel": "全聯",
                            "name": "商品名稱",
                            "pic_url": "https://www.example.com/pic.jpg",
                            "pid": 1,
                            "pno": "123456",
                            "price": 100,
                            "price_unit": 1,
                            "spec": 100,
                            "unit": "g",
                            "url": "https://www.example.com",
                        }
                    ],
                }
            ]
        }
    }


@api.get("/products", tags=["產品"], summary="取得商品列表", response_model=ProductsResponse)
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
    根據指定的商品分類、通路商、查詢字串，回傳商品列表。
    查詢字串可以用空格分隔多個關鍵字，也可以用 "-" 來排除某個關鍵字。
    為了避免資料量過大，預設每次只回傳 10 筆資料。
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
        for keyword in query.split():
            if keyword.startswith("-"):
                keyword = keyword[1:]
                products = products.filter(~Product.name.contains(keyword))
            else:
                products = products.filter(Product.name.contains(keyword))

    total_count = products.count()
    products = products.order_by(Product.price_unit.asc())
    products = products.offset((page - 1) * limit).limit(limit)

    return {
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "products": products.all(),
    }


########################################################################

app.include_router(api, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)
