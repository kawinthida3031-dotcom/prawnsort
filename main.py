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

WORKSPACE_NAME = "kawinthida-uttiya-s-workspace"
WORKFLOW_ID = "prawnsort-1-yolov8s-t2"
API_KEY = os.getenv("ROBOFLOW_API_KEY", "ใส่_API_Key_ของคุณตรงนี้")

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
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
            
        # ==========================================
        # 🧠 Smart Best-Fit Parsing (ไม่มีการบังคับตอบ Stage 1 มั่วๆ อีกต่อไป)
        # ==========================================
        predictions = []
        
        if isinstance(result, dict):
            if "predictions" in result:
                predictions = result["predictions"]
            elif "output" in result and isinstance(result["output"], list):
                predictions = result["output"]
            else:
                for key, val in result.items():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        predictions = val
                        break
        elif isinstance(result, list):
            predictions = result

        # หากตรวจพบวัตถุ ค้นหาตัวที่มีความมั่นใจสูงสุด (Highest Confidence) จริงๆ
        if predictions and len(predictions) > 0:
            best_pred = max(predictions, key=lambda x: x.get('confidence', 0.0))
            
            detected_stage = best_pred.get('class', 'unknown')
            confidence_score = best_pred.get('confidence', 0.0)
            
            return {
                "success": True,
                "stage": detected_stage,
                "confidence": f"{confidence_score * 100:.1f}%",
                "prediction_results": result
            }
        
        # ❌ กรณีไม่พบวัตถุหรือภาพเคลียร์: ห้ามตีกระยอบว่าเป็น Stage 1 เด็ดขาด! 
        # ให้ส่งสถานะชัดเจนว่า "ไม่พบระยะไข่" เพื่อให้หน้าเว็บรู้ว่าไม่มีเป้าหมาย
        return {
            "success": True,
            "stage": "ไม่พบระยะไข่ (No Detection)",
            "confidence": "0.0%",
            "prediction_results": result
        }
        
    except Exception as e:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        raise HTTPException(status_code=500, detail=str(e))