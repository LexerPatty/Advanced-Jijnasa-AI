@echo off
start "AUTH 8000" cmd /k "cd /d P:\Advanced-Jijnasa-AI\backend_auth && python -m uvicorn app.main:app --port 8000 --reload"
start "BACKEND 8001" cmd /k "cd /d P:\Advanced-Jijnasa-AI\Backend && python -m uvicorn main:app --port 8001 --reload"