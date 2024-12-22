import asyncio
import csv
import json

import aiohttp
from bs4 import BeautifulSoup
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio

from crawler import PX_Crawler
from database import Product, create_session, create_table, drop_table


def px_update():
    session = create_session()
    with PX_Crawler() as crawler:
        # products = crawler.get_all_products(save_result=False)

        crawler.process_categories(save_result=False)
        cats = [c for c in crawler.categories.values() if c["level"] == 3]

        for cat in tqdm(cats, desc="PX Mart"):
            for d in crawler.process_goods(cat["id"], save_result=False):
                pid = d["pid"]
                product = session.query(Product).filter(Product.pid == pid).first()
                if product:
                    price, unit = int(d["price"]), product.spec
                    product.price = price
                    product.price_unit = round(price / unit, 4)
                # else:
                #     print(d, "Not found")
    session.commit()
    session.close()


async def cr4_get_product_price(pid):
    async with aiohttp.request("get", f"https://online.carrefour.com.tw/zh/{pid}.html") as resp:
        resp.raise_for_status()
        soup = BeautifulSoup(await resp.text(), "lxml")

    price = soup.select_one("#product-details-form span.money").text

    if not price or not price.isdigit():
        raise ValueError("Price not found")

    return int(price)


async def cr4_update():
    session = create_session()
    products = session.query(Product).filter(Product.channel == "家樂福")

    errors = []

    async for product in tqdm_asyncio(products.all(), desc="Carrefour"):
        try:
            pid = product.pid
            price = await cr4_get_product_price(pid)
            product.price = price
            product.price_unit = round(price / product.spec, 4)
        except KeyboardInterrupt:
            break
        except Exception as e:
            errors.append(pid)
            continue

    print("Errors:")
    print(errors)

    session.commit()
    session.close()


def to_csv():
    session = create_session()
    products = session.query(Product).all()

    with open("products.csv", "w", encoding="utf-8", newline="") as f:
        fieldnames = Product.__table__.columns.keys()
        writer = csv.writer(f)
        writer.writerow(fieldnames)

        for product in products:
            writer.writerow([getattr(product, c) for c in fieldnames])

    session.close()


def from_csv():
    with open("products.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        products = [row for row in reader]

    session = create_session()
    for product in products:
        p = Product(**product)
        session.add(p)
    session.commit()
    session.close()


if __name__ == "__main__":
    # drop_table()
    # create_table()
    px_update()
    asyncio.run(cr4_update())

    # to_csv()
    # from_csv()
