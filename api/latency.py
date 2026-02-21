import json
import statistics
import os
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")

def load_data():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r") as f:
        return json.load(f)

@app.post("/api/latency")
async def get_latency_metrics(payload: dict = Body(...)):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    telemetry_data = load_data()
    
    results = {}
    
    for region in regions:
        region_data = [d for d in telemetry_data if d["region"] == region]
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
