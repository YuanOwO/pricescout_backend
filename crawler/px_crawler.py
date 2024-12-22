import csv
import json
import os
import shutil
from datetime import datetime

import requests
from tqdm import tqdm

from .config import DEFAULT_HEADER, GOODS_FIELDS, TIMEOUT

"https://pxgo.net/444Qp0r"


class PX_Crawler:
    API_URL = "https://mwebapi.pxgo.com.tw/api"
    SHOP_NO = "025700"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADER)
        self.login()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.session.close()

    def path(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.API_URL}{path}"

    def write_json(self, path: str, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def write_csv(self, path: str, fieldname, data):
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldname)
            writer.writeheader()
            writer.writerows(data)

    def post(self, path: str, data):
        url = self.path(path)
        resp = self.session.post(url, json=data, timeout=TIMEOUT)
        resp.raise_for_status()
        if resp.json().get("message", None) not in ("操作成功", "success"):
            print(resp.text)
            raise RuntimeError(f"POST failed: {resp.text}")
        return resp.json()["data"]

    def login(self):
        if hasattr(self, "token"):  # Already logged in, ignore
            print("Already logged in.")
            return

        url = "/member/login"
        data = {"username": "1", "password": "123456"}
        token = self.post(url, data)
        token = token["tokenHead"] + token["token"]
        self.token = token
        self.session.headers.update({"Authorization": token})

    def get_categories(self):
        url = "/category/goodsCategoryQuery"
        data = {"channel": 1, "shopNo": self.SHOP_NO}
        data = self.post(url, data)
        return data

    def get_goods(self, category_id: int):
        url = "/goods/goodsQuery"
        page, offset = 1, 100
        data = {
            "categoryPage": True,
            "categoryPageParams": {
                "categoryId": category_id,
                "saleVolumeSort": "DESC",
            },
            "channel": 1,
            "pageNum": page,
            "pageSize": 100,
            "shopNo": self.SHOP_NO,
        }
        result = self.post(url, data)

        if result["total"] > page * offset:
            page += 1
            data["pageNum"] = page
            r = self.post(url, data)
            result["goods"].extend(r["goods"])

        return result

    def get_detail(self, good_id: str, goods_no: str, goods_barcode: str):
        url = "/goods/getDetail"
        data = {
            "goodsId": good_id,
            "goodsNo": goods_no,
            "goodsBarcode": goods_barcode,
            "channel": 1,
            "shopNo": self.SHOP_NO,
        }

        data = self.post(url, data)
        return data

    CATEGORYS_FIELDS = ("level", "id", "name", "children")

    def process_categories(self, save_result=True):
        cats = self.get_categories()
        # self.write_json('px/raw_category.json', cats)

        data = {}
        LEVELS = ("fristLevelDatas", "secondLevelDatas", "thirdLevelDatas")
        for lvl, k in enumerate(LEVELS, 1):
            for cat in cats[k]:
                d = {"level": lvl}
                d.update(
                    {key: cat.get(key, None) for key in self.CATEGORYS_FIELDS if key != "level" and key != "children"}
                )
                d["children"] = []
                if cat["parentCode"] in data:
                    data[cat["parentCode"]]["children"].append(d["id"])
                data[cat["code"]] = d

        self.categories = {cat["id"]: cat for cat in data.values()}

        if save_result:
            self.write_csv("px/categories.csv", self.CATEGORYS_FIELDS, data.values())

    def process_goods(self, category_id: int, save_result=True):
        if not hasattr(self, "categories"):
            self.process_categories(save_result=False)
        goods = self.get_goods(category_id)
        # self.write_json('px/raw_goods.json', goods)

        data = []
        for good in goods["goods"]:
            d = {
                "barcode": good["goodsBarcode"],
                "pid": good["goodsId"],
                "pno": good["goodsNo"],
                "name": good["goodName"],
                "price": good["goodPrice"],
                "spec": "",
                "unit": good["goodsSpec"],
                # 'keywords': ' '.join([
                #     good['qtCategoryName1'],
                #     good['qtCategoryName2'],
                #     self.categories[category_id]['name']
                # ])
            }
            data.append(d)

        if save_result:
            data.sort(key=lambda x: x["pid"])
            self.write_csv(f"px/goods/goods_{category_id}.csv", GOODS_FIELDS, data)
        return data

    def process_goods_detail(self, good_id: str, goods_no: str, goods_barcode: str):
        detail = self.get_detail(good_id, goods_no, goods_barcode)
        self.write_json("px/raw_detail.json", detail)

    def get_all_products(self, save_result=True):
        if not hasattr(self, "categories"):
            self.process_categories(save_result=False)

        dt = datetime.now()
        products = []
        cats = [c for c in self.categories.values() if c["level"] == 3]

        for cat in tqdm(cats, desc="PX Mart"):
            data = self.process_goods(cat["id"], save_result=False)
            products.extend(data)
            # for d in data:
            #     no = d['pno']
            #     if no in products.keys():
            #         continue
            #         # print(f'Conflict: {no}')
            #     #     products[no]['qtCategoryName3'] += f'||{cat["name"]}123'
            #     else:
            #         products[no] = d

        # print(len(products.keys()))

        # products = list(products.values())

        if save_result:
            self.write_json("px/raw_products.json", products)

            # products.sort(key=lambda x: x['pid'])

            t = {key: "" for key in GOODS_FIELDS}
            t[GOODS_FIELDS[0]] = "更新日期"
            t[GOODS_FIELDS[1]] = dt.strftime("%Y-%m-%d %H:%M:%S")
            products.insert(0, t)

            filename = f'px/products_{dt.strftime("%m%d")}.csv'

            self.write_csv(filename, GOODS_FIELDS, products)
        return products


aaa = set()
data = []


def find_cats(cat, id, parent=""):
    if id in aaa:
        return
    aaa.add(id)
    now = parent + "/" + cat[id]["name"]
    data.append(now)
    for child in cat[id]["children"]:
        find_cats(cat, child, now)


if __name__ == "__main__":
    print("Hello")
    with PX_Crawler() as crawler:
        # crawler.login()
        # print('World')
        # crawler.get_all_goods()
        crawler.process_categories()

        cats = crawler.categories

        for cat in crawler.categories.values():
            find_cats(cats, cat["id"], "/" * (cat["level"] - 1))
        with open("px/cats.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(data))
