from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import requests
import shutil
import os

app = FastAPI(
    title="Prawnsort API",
    description="Macrobrachium lanchesteri egg stage classification system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ดึงค่า API Key จาก Environment Variable ของเซิร์ฟเวอร์ (ปลอดภัยเมื่อขึ้น GitHub/Render)
# หรือใส่รหัสของคุณไว้ในเครื่องหมายคำพูดด้านหลังเผื่อรันเทสบนเครื่อง
WORKSPACE_NAME = "kawinthida-uttiya-s-workspace"
WORKFLOW_ID = "prawnsort-1-rfdetr-small-t1"
API_KEY = os.getenv("ROBOFLOW_API_KEY", "ใส่_API_Key_ของคุณตรงนี้")

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    # เสิร์ฟหน้าเว็บ index.html ให้แสดงผลทันทีเมื่อเข้าเว็บไซต์
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Prawnsort Backend is running successfully!</h1><p>Please ensure index.html is in the project folder.</p>"

@app.post("/predict")
async def predict_egg_stage(file: UploadFile = File(...)):
    temp_image_path = f"temp_{file.filename}"
    with open(temp_image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        url = f"https://serverless.roboflow.com/{WORKSPACE_NAME}/{WORKFLOW_ID}"
        params = {"api_key": API_KEY}
        
        with open(temp_image_path, "rb") as image_file:
            files = {"file": (file.filename, image_file, file.content_type)}
            response = requests.post(url, params=params, files=files)
            result = response.json()
        
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            
        return {
            "success": True,
            "prediction_results": result
        }
        
    except Exception as e:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        return {
            "success": False,
            "error": str(e)
        }