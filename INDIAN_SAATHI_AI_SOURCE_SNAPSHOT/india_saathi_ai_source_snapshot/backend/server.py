from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime, timezone, timedelta
from pathlib import Path
import os, uuid, logging, jwt, bcrypt, shutil, re, asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret-change-me')
JWT_ALG = 'HS256'
JWT_EXP_HOURS = 24 * 7  # 7 days

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

UPLOAD_DIR = ROOT_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="India Saathi AI")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

api = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("india-saathi")

# ---------- Models ----------
class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=6)

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str

class AuthResp(BaseModel):
    token: str
    user: UserOut

class ComplaintCreate(BaseModel):
    title: str
    description: str
    category: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    imageUrl: Optional[str] = None

class StatusUpdate(BaseModel):
    status: Optional[str] = None
    departmentId: Optional[str] = None

# ---------- Utils ----------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False

def make_token(uid: str, role: str) -> str:
    payload = {
        "sub": uid,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXP_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

async def current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    if not creds:
        raise HTTPException(401, "Not authenticated")
    try:
        data = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user = await db.users.find_one({"id": data["sub"]}, {"_id": 0, "passwordHash": 0})
    if not user:
        raise HTTPException(401, "User not found")
    return user

async def require_admin(user=Depends(current_user)):
    if user.get("role") != "ADMIN":
        raise HTTPException(403, "Admin access required")
    return user

def user_out(u: dict) -> UserOut:
    return UserOut(id=u["id"], name=u["name"], email=u["email"], phone=u.get("phone"), role=u["role"])

# ---------- AI Analysis ----------
CATEGORY_TO_DEPT = {
    "POTHOLE": "Road Maintenance", "ROAD": "Road Maintenance",
    "GARBAGE": "Waste Management",
    "STREETLIGHT": "Electrical Department",
    "WATER": "Water Department",
    "DRAINAGE": "Drainage Department",
    "TRAFFIC": "Traffic Department",
    "ANIMAL": "Animal Rescue", "INJURED_ANIMAL": "Animal Rescue",
    "ENVIRONMENT": "Waste Management",
    "OTHER": "Emergency Response",
}

KEYWORD_MAP = [
    (r"\b(pothole|road|broken road|crack)\b", "POTHOLE"),
    (r"\b(garbage|trash|waste|dump|litter)\b", "GARBAGE"),
    (r"\b(streetlight|street light|lamp|light pole|dark street)\b", "STREETLIGHT"),
    (r"\b(water|leak|pipe|supply|tap)\b", "WATER"),
    (r"\b(drainage|drain|sewage|overflow|clogged)\b", "DRAINAGE"),
    (r"\b(traffic|signal|jam|congestion)\b", "TRAFFIC"),
    (r"\b(animal|dog|cow|cat|injured animal)\b", "INJURED_ANIMAL"),
]

EMERGENCY_WORDS = ["danger", "urgent", "emergency", "accident", "injured", "fire", "unsafe", "risk", "hazard", "night"]

def fallback_analyze(title: str, description: str, category_hint: str):
    text = f"{title} {description}".lower()
    detected = None
    if category_hint:
        detected = category_hint.upper().replace(" ", "_").replace("/", "_")
    if not detected or detected == "OTHER":
        for pat, cat in KEYWORD_MAP:
            if re.search(pat, text):
                detected = cat
                break
    detected = detected or "OTHER"

    severity_score = 40
    if any(w in text for w in EMERGENCY_WORDS):
        severity_score += 30
    if detected in ("STREETLIGHT", "DRAINAGE", "WATER", "INJURED_ANIMAL"):
        severity_score += 15
    if detected in ("POTHOLE", "TRAFFIC"):
        severity_score += 10
    priority = max(10, min(98, severity_score + len(description) % 15))

    if priority >= 90:
        severity = "CRITICAL"
    elif priority >= 70:
        severity = "HIGH"
    elif priority >= 40:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    dept = CATEGORY_TO_DEPT.get(detected, "Emergency Response")
    reason_map = {
        "STREETLIGHT": "Potential safety risk due to poor night visibility.",
        "POTHOLE": "Road damage may cause accidents and vehicle damage.",
        "GARBAGE": "Uncollected waste may cause health and hygiene concerns.",
        "WATER": "Water supply issue may affect community access to essential services.",
        "DRAINAGE": "Blocked drainage may cause waterlogging and health risks.",
        "TRAFFIC": "Traffic congestion may cause delays and safety concerns.",
        "INJURED_ANIMAL": "Animal in distress requires prompt rescue attention.",
        "OTHER": "Complaint routed for general review.",
    }
    return {
        "category": detected,
        "confidence": 0.78,
        "severity": severity,
        "priorityScore": priority,
        "department": dept,
        "reason": reason_map.get(detected, "Complaint routed for review."),
    }

async def gemini_analyze(title: str, description: str, category_hint: str):
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        return None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        prompt = f"""You are a civic complaint analyzer for India. Analyze this complaint and return STRICT JSON only.

Title: {title}
Description: {description}
User-selected category: {category_hint}

Return JSON with fields:
- category: one of POTHOLE, GARBAGE, STREETLIGHT, WATER, DRAINAGE, TRAFFIC, ENVIRONMENT, INJURED_ANIMAL, OTHER
- confidence: float 0..1
- severity: CRITICAL|HIGH|MEDIUM|LOW
- priorityScore: integer 0..100
- department: one of "Road Maintenance","Waste Management","Electrical Department","Water Department","Drainage Department","Traffic Department","Animal Rescue","Emergency Response"
- reason: one short sentence explaining priority

Only output raw JSON, no markdown."""
        chat = LlmChat(
            api_key=key,
            session_id=f"analyze-{uuid.uuid4()}",
            system_message="You are a civic complaint analysis engine. Respond with strict JSON only.",
        ).with_model("gemini", "gemini-3-flash-preview")
        resp = await chat.send_message(UserMessage(text=prompt))
        txt = resp if isinstance(resp, str) else str(resp)
        # extract json
        m = re.search(r"\{.*\}", txt, re.DOTALL)
        if not m:
            return None
        import json
        data = json.loads(m.group(0))
        # normalize
        data["category"] = str(data.get("category", "OTHER")).upper()
        data["priorityScore"] = int(data.get("priorityScore", 50))
        data["confidence"] = float(data.get("confidence", 0.8))
        return data
    except Exception as e:
        logger.warning(f"Gemini analyze failed, using fallback: {e}")
        return None

async def analyze_complaint(title: str, description: str, category_hint: str):
    result = await gemini_analyze(title, description, category_hint)
    if not result:
        result = fallback_analyze(title, description, category_hint)
    return result

# ---------- Seed ----------
DEPARTMENTS_SEED = [
    ("Road Maintenance", "Handles potholes, road repair, and street surface issues."),
    ("Waste Management", "Manages garbage collection, sanitation, and hygiene."),
    ("Electrical Department", "Manages streetlights and electrical infrastructure."),
    ("Water Department", "Manages water supply, leaks, and pipeline issues."),
    ("Drainage Department", "Handles drainage, sewage, and waterlogging."),
    ("Traffic Department", "Manages traffic signals, congestion, and road safety."),
    ("Animal Rescue", "Handles injured or stray animal reports."),
    ("Emergency Response", "General emergency and civic response."),
]

async def seed():
    # departments
    for name, desc in DEPARTMENTS_SEED:
        exists = await db.departments.find_one({"name": name})
        if not exists:
            await db.departments.insert_one({
                "id": str(uuid.uuid4()), "name": name, "description": desc,
                "createdAt": now_iso(),
            })
    # demo citizen
    if not await db.users.find_one({"email": "demo@indiasaathi.ai"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "name": "Rahul Sharma",
            "email": "demo@indiasaathi.ai", "phone": "+919999999999",
            "passwordHash": hash_pw("password123"), "role": "CITIZEN",
            "createdAt": now_iso(), "updatedAt": now_iso(),
        })
    # admin
    if not await db.users.find_one({"email": "admin@indiasaathi.ai"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "name": "Admin",
            "email": "admin@indiasaathi.ai", "phone": None,
            "passwordHash": hash_pw("admin123"), "role": "ADMIN",
            "createdAt": now_iso(), "updatedAt": now_iso(),
        })
    # counter for tracking id
    if not await db.counters.find_one({"_id": "complaint"}):
        await db.counters.insert_one({"_id": "complaint", "seq": 0})

async def next_tracking_id() -> str:
    res = await db.counters.find_one_and_update(
        {"_id": "complaint"}, {"$inc": {"seq": 1}}, return_document=True, upsert=True
    )
    seq = res["seq"] if res else 1
    year = datetime.now(timezone.utc).year
    return f"NS-{year}-{seq:06d}"

# ---------- Auth Routes ----------
@api.post("/auth/register", response_model=AuthResp)
async def register(body: RegisterInput):
    if await db.users.find_one({"email": body.email.lower()}):
        raise HTTPException(409, "Email already registered")
    uid = str(uuid.uuid4())
    doc = {
        "id": uid, "name": body.name.strip(),
        "email": body.email.lower(), "phone": body.phone,
        "passwordHash": hash_pw(body.password), "role": "CITIZEN",
        "createdAt": now_iso(), "updatedAt": now_iso(),
    }
    await db.users.insert_one(doc)
    token = make_token(uid, "CITIZEN")
    return AuthResp(token=token, user=user_out(doc))

@api.post("/auth/login", response_model=AuthResp)
async def login(body: LoginInput):
    u = await db.users.find_one({"email": body.email.lower()})
    if not u or not verify_pw(body.password, u["passwordHash"]):
        raise HTTPException(401, "Invalid email or password")
    return AuthResp(token=make_token(u["id"], u["role"]), user=user_out(u))

@api.get("/auth/me", response_model=UserOut)
async def me(user=Depends(current_user)):
    return user_out(user)

# ---------- Departments ----------
@api.get("/departments")
async def list_departments(user=Depends(current_user)):
    docs = await db.departments.find({}, {"_id": 0}).to_list(100)
    return docs

# ---------- Upload ----------
@api.post("/upload")
async def upload_image(file: UploadFile = File(...), user=Depends(current_user)):
    ext = (file.filename or "").split(".")[-1].lower() or "jpg"
    if ext not in ("jpg", "jpeg", "png", "webp"):
        raise HTTPException(400, "Only jpg/png/webp allowed")
    fname = f"{uuid.uuid4()}.{ext}"
    fpath = UPLOAD_DIR / fname
    with open(fpath, "wb") as f:
        content = await file.read()
        if len(content) > 8 * 1024 * 1024:
            raise HTTPException(400, "File too large (max 8MB)")
        f.write(content)
    return {"url": f"/uploads/{fname}"}

# ---------- Complaints ----------
async def _complaint_out(c: dict):
    dept = await db.departments.find_one({"id": c.get("departmentId")}, {"_id": 0}) if c.get("departmentId") else None
    c["department"] = dept
    return c

@api.post("/complaints")
async def create_complaint(body: ComplaintCreate, user=Depends(current_user)):
    ai = await analyze_complaint(body.title, body.description, body.category)
    dept_doc = await db.departments.find_one({"name": ai["department"]})
    tracking = await next_tracking_id()
    cid = str(uuid.uuid4())
    doc = {
        "id": cid, "trackingId": tracking,
        "title": body.title, "description": body.description,
        "category": ai["category"], "severity": ai["severity"],
        "priorityScore": ai["priorityScore"], "status": "AI_VERIFIED",
        "departmentId": dept_doc["id"] if dept_doc else None,
        "departmentName": ai["department"],
        "userId": user["id"],
        "userName": user["name"],
        "latitude": body.latitude, "longitude": body.longitude,
        "address": body.address, "imageUrl": body.imageUrl,
        "aiConfidence": ai["confidence"], "aiReason": ai["reason"],
        "createdAt": now_iso(), "updatedAt": now_iso(),
    }
    await db.complaints.insert_one(doc)
    await db.status_history.insert_one({
        "id": str(uuid.uuid4()), "complaintId": cid,
        "oldStatus": None, "newStatus": "SUBMITTED",
        "updatedBy": user["id"], "createdAt": now_iso(),
    })
    await db.status_history.insert_one({
        "id": str(uuid.uuid4()), "complaintId": cid,
        "oldStatus": "SUBMITTED", "newStatus": "AI_VERIFIED",
        "updatedBy": "system", "createdAt": now_iso(),
    })
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "userId": user["id"],
        "title": "Complaint submitted",
        "message": f"Your complaint {tracking} has been registered and assigned to {ai['department']}.",
        "isRead": False, "createdAt": now_iso(),
    })
    doc.pop("_id", None)
    return await _complaint_out(doc)

@api.get("/complaints")
async def my_complaints(user=Depends(current_user)):
    cur = db.complaints.find({"userId": user["id"]}, {"_id": 0}).sort("createdAt", -1)
    docs = await cur.to_list(500)
    for d in docs:
        await _complaint_out(d)
    return docs

@api.get("/complaints/{cid}")
async def complaint_detail(cid: str, user=Depends(current_user)):
    c = await db.complaints.find_one({"id": cid}, {"_id": 0})
    if not c:
        raise HTTPException(404, "Complaint not found")
    if user["role"] != "ADMIN" and c["userId"] != user["id"]:
        raise HTTPException(403, "Forbidden")
    await _complaint_out(c)
    history = await db.status_history.find({"complaintId": cid}, {"_id": 0}).sort("createdAt", 1).to_list(100)
    c["history"] = history
    return c

# ---------- Notifications ----------
@api.get("/notifications")
async def list_notifications(user=Depends(current_user)):
    docs = await db.notifications.find({"userId": user["id"]}, {"_id": 0}).sort("createdAt", -1).to_list(200)
    return docs

@api.post("/notifications/{nid}/read")
async def mark_read(nid: str, user=Depends(current_user)):
    await db.notifications.update_one({"id": nid, "userId": user["id"]}, {"$set": {"isRead": True}})
    return {"ok": True}

@api.post("/notifications/read-all")
async def mark_all_read(user=Depends(current_user)):
    await db.notifications.update_many({"userId": user["id"]}, {"$set": {"isRead": True}})
    return {"ok": True}

# ---------- Admin ----------
@api.get("/admin/stats")
async def admin_stats(user=Depends(require_admin)):
    total = await db.complaints.count_documents({})
    critical = await db.complaints.count_documents({"severity": "CRITICAL"})
    pending = await db.complaints.count_documents({"status": {"$in": ["SUBMITTED", "AI_VERIFIED", "ASSIGNED"]}})
    in_progress = await db.complaints.count_documents({"status": "IN_PROGRESS"})
    resolved = await db.complaints.count_documents({"status": "RESOLVED"})
    return {
        "total": total, "critical": critical, "pending": pending,
        "inProgress": in_progress, "resolved": resolved,
    }

@api.get("/admin/complaints")
async def admin_complaints(user=Depends(require_admin)):
    cur = db.complaints.find({}, {"_id": 0}).sort([("priorityScore", -1), ("createdAt", -1)])
    docs = await cur.to_list(1000)
    for d in docs:
        await _complaint_out(d)
    return docs

@api.get("/admin/complaints/{cid}")
async def admin_complaint(cid: str, user=Depends(require_admin)):
    c = await db.complaints.find_one({"id": cid}, {"_id": 0})
    if not c:
        raise HTTPException(404, "Not found")
    await _complaint_out(c)
    history = await db.status_history.find({"complaintId": cid}, {"_id": 0}).sort("createdAt", 1).to_list(100)
    c["history"] = history
    citizen = await db.users.find_one({"id": c["userId"]}, {"_id": 0, "passwordHash": 0})
    c["citizen"] = citizen
    return c

VALID_STATUSES = ["SUBMITTED", "AI_VERIFIED", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]

@api.patch("/admin/complaints/{cid}")
async def admin_update_complaint(cid: str, body: StatusUpdate, user=Depends(require_admin)):
    c = await db.complaints.find_one({"id": cid})
    if not c:
        raise HTTPException(404, "Not found")
    updates = {"updatedAt": now_iso()}
    old_status = c.get("status")
    changed_status = False
    if body.status:
        if body.status not in VALID_STATUSES:
            raise HTTPException(400, "Invalid status")
        updates["status"] = body.status
        changed_status = body.status != old_status
    dept_changed = False
    if body.departmentId:
        dept = await db.departments.find_one({"id": body.departmentId})
        if not dept:
            raise HTTPException(400, "Invalid department")
        updates["departmentId"] = dept["id"]
        updates["departmentName"] = dept["name"]
        dept_changed = c.get("departmentId") != dept["id"]
    await db.complaints.update_one({"id": cid}, {"$set": updates})
    if changed_status:
        await db.status_history.insert_one({
            "id": str(uuid.uuid4()), "complaintId": cid,
            "oldStatus": old_status, "newStatus": body.status,
            "updatedBy": user["id"], "createdAt": now_iso(),
        })
        pretty = body.status.replace("_", " ").title()
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "userId": c["userId"],
            "title": "Complaint status updated",
            "message": f"Your complaint {c['trackingId']} is now {pretty}.",
            "isRead": False, "createdAt": now_iso(),
        })
    if dept_changed:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "userId": c["userId"],
            "title": "Department assigned",
            "message": f"Your complaint {c['trackingId']} has been assigned to {updates['departmentName']}.",
            "isRead": False, "createdAt": now_iso(),
        })
    updated = await db.complaints.find_one({"id": cid}, {"_id": 0})
    await _complaint_out(updated)
    return updated

# ---------- Health ----------
@api.get("/")
async def root():
    return {"service": "india-saathi-ai", "status": "ok"}

app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await seed()
    logger.info("Startup: seed complete")

@app.on_event("shutdown")
async def on_shutdown():
    client.close()
