# backend/main.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import json
from datetime import datetime

app = FastAPI(title="TaskFlow API", version="1.0.0")

# CORS Configuration (agar frontend bisa akses API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Di production, ganti dengan domain frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models untuk validasi data
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"  # pending, in-progress, completed

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    created_at: str
    updated_at: Optional[str] = None

# Database Helper Functions
DB_PATH = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Agar hasil query bisa diakses seperti dictionary
    return conn

def init_db():
    """Membuat tabel tasks jika belum ada"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Inisialisasi database saat aplikasi start
@app.on_event("startup")
async def startup_event():
    init_db()
    print("Database initialized!")

# ========== API Endpoints ==========

@app.get("/")
async def root():
    return {"message": "Selamat datang di TaskFlow API", "docs": "/docs"}

@app.post("/api/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate):
    """Membuat tugas baru"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tasks (title, description, status)
        VALUES (?, ?, ?)
    """, (task.title, task.description, task.status))
    
    task_id = cursor.lastrowid
    conn.commit()
    
    # Ambil data yang baru saja diinsert
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    new_task = dict(cursor.fetchone())
    conn.close()
    
    return new_task

@app.get("/api/tasks", response_model=List[Task])
async def get_all_tasks():
    """Mendapatkan semua tugas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY id DESC")
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

@app.get("/api/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int):
    """Mendapatkan detail satu tugas berdasarkan ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()
    
    if not task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")
    
    return dict(task)

@app.put("/api/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task_update: TaskCreate):
    """Memperbarui tugas yang sudah ada"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cek apakah tugas ada
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")
    
    # Update tugas
    cursor.execute("""
        UPDATE tasks 
        SET title = ?, description = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (task_update.title, task_update.description, task_update.status, task_id))
    
    conn.commit()
    
    # Ambil data terbaru
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated_task = dict(cursor.fetchone())
    conn.close()
    
    return updated_task

@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    """Menghapus tugas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")
    
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)