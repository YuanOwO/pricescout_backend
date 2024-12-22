uvicorn main:app --host 0.0.0.0 --port 5050 --reload
cloudflared tunnel --url localhost:5050
