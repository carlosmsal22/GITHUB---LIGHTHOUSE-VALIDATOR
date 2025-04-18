
import os
import sqlite3
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def read_root():
    return {"message": "Lighthouse Validator is live and ready 🚀"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    password = request.query_params.get("password")
    if password != os.getenv("DASHBOARD_PASSWORD"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/validate-image")
async def validate_image(request: Request):
    body = await request.json()
    media_url = body.get("media_url")
    respondent_id = body.get("respondent_id", "unknown")
    geo = {}
    ip = request.client.host
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}").json()
        geo = {"country": r.get("country"), "region": r.get("regionName")}
    except:
        pass
    conn = sqlite3.connect("logs.db")
    conn.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, respondent TEXT, ip TEXT, country TEXT, region TEXT)")
    conn.execute("INSERT INTO logs (respondent, ip, country, region) VALUES (?, ?, ?, ?)", (respondent_id, ip, geo.get("country"), geo.get("region")))
    conn.commit()
    conn.close()
    return {"status": "validated", "ip": ip, "geo": geo}

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print("Received webhook:", body)
    return {"status": "received"}
