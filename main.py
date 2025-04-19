import os
import io
import sqlite3
import requests
import imagehash
import numpy as np
import torch
import PIL.Image
import cv2

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from transformers import CLIPProcessor, CLIPModel

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load CLIP model once
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

PROMPTS = ["person cleaning", "vacuuming", "household task", "cleaning a room"]

def is_blurry(img):
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
    score = cv2.Laplacian(gray, cv2.CV_64F).var()
    return score < 100  # threshold for blur

def check_clip_relevance(img):
    inputs = clip_processor(text=PROMPTS, images=img, return_tensors="pt", padding=True)
    outputs = clip_model(**inputs)
    scores = outputs.logits_per_image.softmax(dim=1).detach().numpy()[0]
    return float(np.max(scores)), PROMPTS[np.argmax(scores)]

@app.get("/")
def root():
    return {"message": "Lighthouse Validator is live and ready 🚀"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    password = request.query_params.get("password")
    if password != os.getenv("DASHBOARD_PASSWORD"):
        raise HTTPException(status_code=403)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/validate-image")
async def validate_image(request: Request):
    body = await request.json()
    media_url = body.get("media_url")
    respondent_id = body.get("respondent_id", "unknown")
    ip = request.client.host

    # Step 1: Download image
   try:
    response = requests.get(media_url, headers={"User-Agent": "Mozilla/5.0"})
    img = PIL.Image.open(io.BytesIO(response.content)).convert("RGB")
except Exception as e:
    return {
        "valid": False,
        "reasons": ["Could not download image"],
        "error": str(e)
    }


    except Exception as e:
        return {"valid": False, "reasons": ["Could not download image"], "error": str(e)}

    reasons = []
    score, matched_prompt = check_clip_relevance(img)
    if score < 0.30:
        reasons.append("Not relevant to prompt")

    if is_blurry(img):
        reasons.append("Image is blurry")

    # Placeholder hash database (no duplicate detection yet)
    phash_val = str(imagehash.phash(img))

    # Geo lookup
    geo = {}
    try:
        geo_resp = requests.get(f"http://ip-api.com/json/{ip}").json()
        geo = {"country": geo_resp.get("country"), "region": geo_resp.get("regionName")}
    except:
        pass

    # Store log
    conn = sqlite3.connect("logs.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY,
        respondent TEXT,
        ip TEXT,
        country TEXT,
        region TEXT,
        valid INTEGER,
        clip_score REAL,
        phash TEXT,
        reasons TEXT
    )""")
    conn.execute("INSERT INTO logs (respondent, ip, country, region, valid, clip_score, phash, reasons) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                 (respondent_id, ip, geo.get("country"), geo.get("region"), int(len(reasons)==0), score, phash_val, ", ".join(reasons)))
    conn.commit()
    conn.close()

    return {
        "valid": len(reasons) == 0,
        "reasons": reasons,
        "score": round(score, 2),
        "matched_prompt": matched_prompt,
        "geo": geo
    }

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print("Received webhook:", body)
    return {"status": "received"}
