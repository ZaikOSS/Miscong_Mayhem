import os
import shutil
from fastapi import FastAPI, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# [M2] Debug mode enabled in production
# [M10] Default FastAPI docs (Swagger UI) exposed at /docs
app = FastAPI(debug=True, title="SharePy Vulnerable App")

# [M7] CORS Wildcard - Allows any website to fetch data from your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# [M15] Weak JWT Secret used for signing tokens
SECRET_KEY = "changeme"
ALGORITHM = "HS256"

# [M6] Hardcoded AWS/MinIO keys in the code
MINIO_USER = "minioadmin"
MINIO_PASS = "minioadmin"

@app.get("/")
def read_root():
    return FileResponse('index.html')

# [M14] Endpoint that dumps the entire environment (including .env secrets)
@app.get("/debug/info")
def debug_info():
    return os.environ

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(user: UserLogin, response: Response):
    # [M1] Checking against hardcoded password (conceptually)
    if user.username == "admin" and user.password == "admin123":
        token = "fake-jwt-token-changeme"
        
        # [M9] Cookies without Secure, HttpOnly, or SameSite=Strict
        response.set_cookie(
            key="session_id",
            value=token,
            httponly=False,  # JS can read this (XSS risk)
            secure=False,    # Sent over plain HTTP
            samesite="Lax"   # Not Strict
        )
        return {"msg": "Logged in as Admin!", "token": token}
    return {"msg": "Login failed"}

# [M13] Vulnerable Upload Endpoint (Added for Auto-Exploit)
# It allows uploading ANY file (even viruses) to the 777 folder
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"/app/uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}
