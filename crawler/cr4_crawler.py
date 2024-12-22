import csv
import json
import os
from datetime import datetime
from typing import Self

import requests
from bs4 import BeautifulSoup

# from slugify import slugify
from tqdm import tqdm

from .config import DEFAULT_HEADER, GOODS_FIELDS, TIMEOUT


class CR4_Crawler:
    BASED_URL = "https://online.carrefour.com.tw"

    def __init__(self) -> None:
        self.now = datetime.now()
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADER)
        self.FOLODER = f'carrefour_{self.now.strftime("%m%d")}/'

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        self.session.close()

    @staticmethod
    def slugify(text: str) -> str:
        replacements = [(" ", "-"), ("$", "%24"), ("&", "and"), ("(", "%28"), (")", "%29"), ("/", "%2F"), ("．", "")]
        for a, b in replacements:
            text = text.replace(a, b)
        return text
        # return slugify(text, allow_unicode=True, replacements=replacements)

    def write_json(self, file: str, data) -> None:
        file = self.FOLODER + file
        d, f = os.path.split(file)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def write_csv(self, file: str, data, fields) -> None:
        file = self.FOLODER + file
        d, f = os.path.split(file)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fields)
            writer.writeheader()
            writer.writerows(data)

    def get(self, path: str, *, params=None, **kwargs) -> BeautifulSoup:
        url = self.BASED_URL + path
        resp = self.session.get(url, timeout=TIMEOUT, params=params, **kwargs)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        return soup

    def process_categories(self, save_result=True):
        soup = self.get("/")
        data = {}

        level1 = soup.find_all(class_="first-level-item")
        for item in level1:
            name = item.text.strip()
            cid = item["data-cgid"]
            data[cid] = {"name": name, "children": {}}

        level2 = soup.find_all(class_="second-level-wrapper")
        for item in level2:
            cid = item["class"][1]
            # print(cid)
            for item in item.find_all("li"):
                name = item.text.strip()
                cid2 = item["id"]
                data[cid]["children"][cid2] = {"name": name, "children": []}

        level3 = soup.find_all(class_="third-level")
        for item in level3:
            cid = item["class"][1]
            # print(cid)
            for item2 in item.find_all(class_="third-level-block"):
                cid2 = item2["class"][1]
                for item3 in item2.find_all(class_="item"):
                    name = item3.text.strip()
                    data[cid]["children"][cid2]["children"].append(name)

        self.categories = data

        if save_result:
            self.write_json("categories.json", data)
        return data

    GOODS_FIELDS = ("pid", "name", "price", "variant", "brand", "category")

    def get_goods(self, cat_path: str, position=None, save_result=True):
        url = "/zh/" + cat_path
        soup = self.get(url)
        # print(soup.title)
        total_count = int(soup.find(class_="resultCount number").text.strip())

        data = []

        with tqdm(total=total_count, desc=cat_path + ": ", position=None, leave=False) as pbar:
            while len(data) < total_count:
                soup = self.get(url, params={"start": len(data)})
                items = soup.find_all(class_="hot-recommend-item")
                for item in items:
                    info = item.select_one(".box-img > a")
                    d = {
                        "barcode": "",
                        "pid": info["data-pid"],
                        "pno": "",
                        "name": info["data-name"],
                        "price": info["data-price"],
                        "spec": "",
                        "unit": info["data-variant"],
                        "keywords": " ".join(
                            [
                                info["data-brand"],
                                info["data-category"],
                            ]
                        ),
                    }
                    data.append(d)
                    pbar.update(1)

        data.sort(key=lambda x: x["pid"])

        # print(data)

        if save_result:
            self.write_csv(f"{cat_path}.csv", data, GOODS_FIELDS)
        return data

    def get_all_products(self, categories=None):
        stop = False
        errors = []
        if categories is None:
            if not hasattr(self, "categories"):
                self.process_categories(save_result=False)
            cats = self.categories
        else:
            cats = categories

        for cat1 in tqdm(cats.values(), desc="Carrefour", position=0):
            data = []
            cn1 = cat1["name"]
            if cn1 == "好康主題":
                continue
            for cat2 in tqdm(cat1["children"].values(), desc=cn1, position=1, leave=False):
                cn2 = cat2["name"]
                for cat3 in tqdm(cat2["children"], desc=cn1 + "/" + cn2, position=2, leave=False):
                    cn3 = cat3
                    cats = map(self.slugify, (cn1, cn2, cn3))
                    cat_path = "/".join(cats)
                    try:
                        self.get_goods(cat_path, position=3)
                        # write_csv(f'{cat_path}.csv', d, GOODS_FIELDS)
                    except KeyboardInterrupt:
                        stop = True
                        break
                    except Exception as e:
                        errors.append([cn1, cn2, cn3, str(e)])
                    # stop = True
                    # break
                if stop:
                    break
            if stop:
                break

        print("Errors:")
        print(errors)
        self.write_json("debug.json", {"time": self.now.isoformat(), "errors": errors})


# def load_error():
#     with open('carrefour/debug.json', 'r', encoding='utf-8') as f:
#         data = json.load(f)['errors']
#     for cat in data:
#         cat_path = '/'.join(map(my_slugify, cat))
#         print(cat_path)
#         d = get_goods(cat_path)
#         write_csv(f'{cat_path}.csv', d, GOODS_FIELDS)


# load_error()
