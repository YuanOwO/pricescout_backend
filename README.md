# PriceScout Backend

超市商品比價網 後端資料庫

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
