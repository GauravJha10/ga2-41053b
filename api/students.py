import csv
import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Relative to the script location on Vercel
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), "q-fastapi.csv")

def load_students():
    students = []
    if not os.path.exists(CSV_FILE_PATH):
        return students
    with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            students.append({"studentId": int(row["studentId"]), "class": row["class"]})
    return students

@app.get("/api/students")
async def get_students(class_name: Optional[List[str]] = Query(None, alias="class")):
    all_students = load_students()
    if not class_name:
        return {"students": all_students}
    filtered_students = [s for s in all_students if s["class"] in class_name]
    return {"students": filtered_students}
