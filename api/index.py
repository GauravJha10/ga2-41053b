import csv
import json
import statistics
import os
from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

app = FastAPI()

# Enable CORS for GET and POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directory for data files (same as api/ on Vercel)
DATA_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(DATA_DIR, "q-fastapi.csv")
JSON_PATH = os.path.join(DATA_DIR, "q-vercel-latency.json")

def load_students():
    students = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                students.append({"studentId": int(row["studentId"]), "class": row["class"]})
    return students

def load_telemetry():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            return json.load(f)
    return []

@app.get("/api/students")
async def get_students(class_name: Optional[List[str]] = Query(None, alias="class")):
    all_students = load_students()
    if not class_name:
        return {"students": all_students}
    filtered_students = [s for s in all_students if s["class"] in class_name]
    return {"students": filtered_students}

@app.post("/api/latency")
async def get_latency_metrics(payload: dict = Body(...)):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    
    data = load_telemetry()
    results = {}
    
    for region in regions:
        region_data = [d for d in data if d["region"] == region]
        if not region_data:
            continue
            
        latencies = [d["latency_ms"] for d in region_data]
        uptimes = [d["uptime_pct"] for d in region_data]
        
        avg_latency = statistics.mean(latencies) if latencies else 0
        if len(latencies) >= 2:
            p95_latency = statistics.quantiles(latencies, n=100)[94]
        elif latencies:
            p95_latency = latencies[0]
        else:
            p95_latency = 0
            
        avg_uptime = statistics.mean(uptimes) if uptimes else 0
        breaches = sum(1 for l in latencies if l > threshold)
        
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": breaches
        }
        
    return results

@app.get("/")
async def root():
    return {"status": "ok", "message": "FastAPI on Vercel is running."}
