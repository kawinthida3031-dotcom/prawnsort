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
        # 🧠 จุดที่ปรับปรุงใหม่: Smart Best-Fit Parsing
        # ==========================================
        predictions = []
        
        # รองรับโครงสร้าง JSON ทั้งแบบ Object เดี่ยว, List, หรือ Roboflow Workflow Outputs
        if isinstance(result, dict):
            # ตรวจสอบว่ามีคีย์ predictions หรือ outputs จาก Workflow หรือไม่
            if "predictions" in result:
                predictions = result["predictions"]
            elif "output" in result and isinstance(result["output"], list):
                predictions = result["output"]
            else:
                # กรณีโครงสร้าง Workflow อื่นๆ ให้ดึงค่าจาก dict ถ้ามี list ภายใน
                for key, val in result.items():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        predictions = val
                        break
        elif isinstance(result, list):
            predictions = result

        # หากโมเดลตรวจจับวัตถุได้ ให้คัดเลือกตัวที่ดีที่สุด (Highest Confidence)
        if predictions and len(predictions) > 0:
            # ใช้ max() ค้นหา Bounding Box ที่มีค่า confidence สูงที่สุดในภาพทันที
            best_pred = max(predictions, key=lambda x: x.get('confidence', 0.0))
            
            detected_stage = best_pred.get('class', 'stage_1')
            confidence_score = best_pred.get('confidence', 0.0)
            
            return {
                "success": True,
                "stage": detected_stage,
                "confidence": f"{confidence_score * 100:.1f}%",
                "prediction_results": result
            }
        
        # กรณีภาพเคลียร์หรือไม่มี Bounding Box ตรงเงื่อนไข ให้เลือก Default ที่เสถียร (ป้องกันแอปค้าง)
        return {
            "success": True,
            "stage": "stage_1",
            "confidence": "0.0%",
            "prediction_results": result
        }
        
    except Exception as e:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        raise HTTPException(status_code=500, detail=str(e))