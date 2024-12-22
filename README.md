# PriceScout Backend

超市商品比價網 後端資料庫

## 簡介

我們的平台旨在為消費者提供一個便捷的價格比較工具，類似於超市商品標籤上標註每百克價格的方式，讓使用者快速找到最划算的選項。不過，我們的服務不僅限於單一超市，而是整合了[全聯福利中心](https://www.pxmart.com.tw/)、[家樂福](https://www.carrefour.com.tw/)等多家超市的商品資訊，協助使用者在購物前就能全面掌握市場價格。

我們的專案將前後端分開，這裡是後端部分，前端部分請參考[這個連結](https://github.com/YuanOwO/pricescout)。

## 使用技術

-   FastAPI
    使用 FastAPI 建立 RESTful API 服務
-   SQLAlchemy
    使用 SQLAlchemy 連接資料庫，並進行資料操作
-   SQLite
    使用 SQLite 作為資料庫儲存資料

## 安裝與使用

1.  下載此專案
    ```bash
    git clone https://github.com/YuanOwO/pricescout_backend.git
    cd pricescout_backend
    ```
2.  確認已安裝 Python 3.12 以上版本
3.  安裝相依套件
    ```bash
    pip install -r requirements.txt
    ```
4.  執行 API 服務
    預設使用 `port 5050` 啟動服務，可自行調整。
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 5050
    ```
5.  進入 `http://localhost:5050/api/v1/docs` 即可看到 API 文件
