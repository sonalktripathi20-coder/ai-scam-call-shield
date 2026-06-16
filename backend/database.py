"""
database.py - SQLite ORM using SQLAlchemy
Stores call sessions, risk scores, transcripts, and actions taken.
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Boolean, Text, event
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.getenv("DB_PATH", os.path.join(BASE_DIR, "scam_shield.db"))

# Vercel serverless environments have a read-only filesystem except for /tmp
if os.getenv("VERCEL"):
    DB_PATH = "/tmp/scam_shield.db"

try:
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
except Exception as e:
    print(f"[WARN] SQLite file-based database at {DB_PATH} failed to initialize ({e}). Falling back to in-memory database.")
    DB_PATH = ":memory:"
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

# Enable WAL mode if possible, always enable foreign keys
@event.listens_for(engine, "connect")
def _set_wal(dbapi_conn, _):
    if DB_PATH != ":memory:":
        try:
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
        except Exception as e:
            print(f"[WARN] Failed to set WAL mode: {e}")
    try:
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
    except Exception as e:
        print(f"[WARN] Failed to enable foreign keys: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────

class CallSession(Base):
    __tablename__ = "call_sessions"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(String(64), default="default_user", index=True)
    call_sid    = Column(String(64), unique=True, index=True, nullable=False)
    from_number = Column(String(20))
    to_number   = Column(String(20))
    direction   = Column(String(16), default="inbound")  # inbound | outbound

    started_at  = Column(DateTime, default=datetime.utcnow)
    ended_at    = Column(DateTime, nullable=True)
    duration_s  = Column(Integer, nullable=True)

    # Final risk assessment
    final_score = Column(Float, default=0.0)
    risk_label  = Column(String(16), default="safe")  # safe|suspicious|fraud
    status      = Column(String(16), default="active")  # active|completed|blocked

    # AI Voice Analysis
    aiVoiceScore          = Column(Float, default=0.0)
    humanVoiceProbability = Column(Float, default=0.0)
    aiVoiceProbability    = Column(Float, default=0.0)
    voiceClassification   = Column(String(32), default="Uncertain")
    voiceConfidence       = Column(Float, default=0.0)

    # Transcript
    full_transcript = Column(Text, default="")

    # Explainable AI (XAI) parameters
    xai_risk_factors  = Column(Text, default="[]") # JSON list of reasons/weights/scores
    mitigation_advice = Column(Text, default="")
    reputation_score  = Column(Float, default=0.0)

    # Action taken
    action_taken   = Column(String(32), nullable=True)  # warning_injected|hung_up|none
    action_at      = Column(DateTime, nullable=True)

    # App settings at time of call
    threshold_used = Column(Float, default=0.71)
    auto_hangup    = Column(Boolean, default=True)


class ScoreEvent(Base):
    """Rolling score snapshots during a call (for graphing in the app)."""
    __tablename__ = "score_events"

    id         = Column(Integer, primary_key=True, index=True)
    call_sid   = Column(String(64), index=True, nullable=False)
    timestamp  = Column(DateTime, default=datetime.utcnow)
    score      = Column(Float, nullable=False)
    label      = Column(String(16), nullable=False)
    transcript_chunk = Column(Text, default="")


class AppSettings(Base):
    """Global app configuration per user."""
    __tablename__ = "app_settings"

    id               = Column(Integer, primary_key=True)
    user_id          = Column(String(64), default="default_user", unique=True, index=True)
    risk_threshold   = Column(Float, default=0.71)
    auto_hangup      = Column(Boolean, default=True)
    alert_suspicious = Column(Boolean, default=True)
    unknown_only     = Column(Boolean, default=True)   # Only monitor unknown numbers
    forward_to       = Column(String(20), nullable=True)  # user's real number
    expo_push_token  = Column(String(100), nullable=True)  # Expo push token from app
    updated_at       = Column(DateTime, default=datetime.utcnow)


class SavedContact(Base):
    """Phone contacts synced from the mobile app (stored as SHA-256 hashes for privacy)."""
    __tablename__ = "saved_contacts"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(String(64), default="default_user", index=True)
    phone_hash  = Column(String(64), index=True, nullable=False)
    synced_at   = Column(DateTime, default=datetime.utcnow)


class VoiceProfile(Base):
    """Enrolled voice identity profiles for voice vault analysis."""
    __tablename__ = "voice_profiles"

    id       = Column(Integer, primary_key=True, index=True)
    user_id  = Column(String(64), default="default_user", index=True)
    name     = Column(String(100), nullable=False)
    role     = Column(String(50), nullable=False)
    phone    = Column(String(50), nullable=False)
    hash     = Column(String(100), nullable=False)
    status   = Column(String(50), default="Voice Authenticated")
    features = Column(String(200), nullable=True)
    date     = Column(String(100), nullable=True)
    audio_data = Column(Text, nullable=True)


class ReputationReport(Base):
    """Stores spam flags and reputation details for incoming phone numbers."""
    __tablename__ = "reputation_reports"

    id           = Column(Integer, primary_key=True, index=True)
    phone        = Column(String(20), unique=True, index=True, nullable=False)  # Normalized number
    flag_count   = Column(Integer, default=0)
    reports_list = Column(Text, default="[]")  # JSON string of individual reports
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Create all tables and seed default settings. Recreates db on schema mismatch."""
    from sqlalchemy.exc import OperationalError
    
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            # Force schema validation to trigger OperationalError on mismatch
            db.query(CallSession).first()
            db.query(VoiceProfile).first()
            
            if not db.query(AppSettings).filter_by(user_id="default_user").first():
                db.add(AppSettings(user_id="default_user"))
                db.commit()
                
            if not db.query(VoiceProfile).filter_by(user_id="default_user").first():
                db.add(VoiceProfile(
                    user_id="default_user",
                    name="Sonal Tripathi",
                    role="Son",
                    phone="+91 70192 38491",
                    hash="98a3b50c18d9f4e2...",
                    status="Voice Authenticated",
                    date="June 12, 2026",
                    features="Pitch: 142.4Hz, HNR: 11.4dB",
                    audio_data="/static/sample_audio.wav"
                ))
                db.add(VoiceProfile(
                    user_id="default_user",
                    name="Family Backup Desk",
                    role="Backup",
                    phone="+91 80012 34567",
                    hash="41b2c3d4e5f6a7b8...",
                    status="Vault Enrolled",
                    date="June 13, 2026",
                    features="Pitch: 210.8Hz, HNR: 14.8dB"
                ))
                db.commit()
        finally:
            db.close()
    except OperationalError as e:
        print(f"[DB] Schema mismatch detected ({e}). Recreating database...")
        # Close engine connection pool
        engine.dispose()
        # Drop all tables first, then recreate
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            db.add(AppSettings(user_id="default_user"))
            db.add(VoiceProfile(
                user_id="default_user",
                name="Sonal Tripathi",
                role="Son",
                phone="+91 70192 38491",
                hash="98a3b50c18d9f4e2...",
                status="Voice Authenticated",
                date="June 12, 2026",
                features="Pitch: 142.4Hz, HNR: 11.4dB",
                audio_data="/static/sample_audio.wav"
            ))
            db.add(VoiceProfile(
                user_id="default_user",
                name="Family Backup Desk",
                role="Backup",
                phone="+91 80012 34567",
                hash="41b2c3d4e5f6a7b8...",
                status="Vault Enrolled",
                date="June 13, 2026",
                features="Pitch: 210.8Hz, HNR: 14.8dB"
            ))
            db.commit()
        finally:
            db.close()
        print("[DB] Database successfully recreated with new schema.")


def is_known_number(db: Session, phone: str) -> bool:
    """
    Normalize and check if the SHA-256 hash of a phone number matches saved contacts.
    Strips spaces, dashes, +91 country code variations.
    """
    import re
    import hashlib

    def normalize(n: str) -> str:
        n = re.sub(r'[^\d]', '', str(n))  # digits only
        if len(n) == 12 and n.startswith('91'):
            n = n[2:]  # strip 91 country code
        if len(n) == 11 and n.startswith('0'):
            n = n[1:]  # strip leading 0
        return n[-10:]  # last 10 digits

    normalized_input = normalize(phone)
    hashed_input = hashlib.sha256(normalized_input.encode('utf-8')).hexdigest()
    
    # Direct indexed lookup for optimal scaling
    exists = db.query(SavedContact).filter_by(phone_hash=hashed_input).first() is not None
    return exists


def get_db() -> Session:
    """FastAPI dependency: yield a db session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────
# Helper functions (used by main.py)
# ─────────────────────────────────────────────

def create_call(db: Session, call_sid: str, from_num: str, to_num: str,
                settings: AppSettings) -> CallSession:
    user_id = getattr(settings, "user_id", "default_user")
    call = CallSession(
        user_id        = user_id,
        call_sid       = call_sid,
        from_number    = from_num,
        to_number      = to_num,
        threshold_used = settings.risk_threshold,
        auto_hangup    = settings.auto_hangup,
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def update_call_score(
    db: Session,
    call_sid: str,
    score: float,
    label: str,
    transcript_chunk: str,
    xai_risk_factors: str = None,
    mitigation_advice: str = None
):
    db.add(ScoreEvent(
        call_sid=call_sid, score=score, label=label,
        transcript_chunk=transcript_chunk
    ))
    # Update the call's final score if this is higher (worst-case tracking)
    call = db.query(CallSession).filter_by(call_sid=call_sid).first()
    if call:
        if call.full_transcript:
            call.full_transcript += " " + transcript_chunk
        else:
            call.full_transcript = transcript_chunk

        if score > call.final_score:
            call.final_score = score
            call.risk_label  = label

        if xai_risk_factors:
            call.xai_risk_factors = xai_risk_factors
        if mitigation_advice:
            call.mitigation_advice = mitigation_advice
    db.commit()


def close_call(db: Session, call_sid: str, action: str = "none"):
    call = db.query(CallSession).filter_by(call_sid=call_sid).first()
    if call:
        call.ended_at    = datetime.utcnow()
        call.status      = "blocked" if action in ("warning_injected", "hung_up") else "completed"
        call.action_taken = action
        if action != "none":
            call.action_at = datetime.utcnow()
        db.commit()


# ─────────────────────────────────────────────
# Reputation Helper Functions
# ─────────────────────────────────────────────
def get_reputation(db: Session, phone: str) -> dict:
    """Get spam flags and reputation history for a number. Returns default if not found."""
    import re
    import json
    
    def normalize(n: str) -> str:
        n = re.sub(r'[^\d]', '', str(n))  # digits only
        if len(n) == 12 and n.startswith('91'): n = n[2:]
        if len(n) == 11 and n.startswith('0'):  n = n[1:]
        return n[-10:]  # last 10 digits
        
    norm_phone = normalize(phone)
    rep = db.query(ReputationReport).filter_by(phone=norm_phone).first()
    if not rep:
        return {
            "phone": phone,
            "flag_count": 0,
            "reports": [],
            "reputation_label": "safe"
        }
        
    try:
        reports = json.loads(rep.reports_list)
    except Exception:
        reports = []
        
    # Classify reputation based on report counts
    label = "safe"
    if rep.flag_count >= 10:
        label = "fraud"
    elif rep.flag_count >= 3:
        label = "suspicious"
        
    return {
        "phone": norm_phone,
        "flag_count": rep.flag_count,
        "reports": reports,
        "reputation_label": label
    }


def add_spam_flag(db: Session, phone: str, category: str, comment: str):
    """Add a spam report for a phone number."""
    import re
    import json
    
    def normalize(n: str) -> str:
        n = re.sub(r'[^\d]', '', str(n))
        if len(n) == 12 and n.startswith('91'): n = n[2:]
        if len(n) == 11 and n.startswith('0'):  n = n[1:]
        return n[-10:]
        
    norm_phone = normalize(phone)
    rep = db.query(ReputationReport).filter_by(phone=norm_phone).first()
    
    new_report = {
        "category": category,
        "comment": comment,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if not rep:
        rep = ReputationReport(
            phone=norm_phone,
            flag_count=1,
            reports_list=json.dumps([new_report])
        )
        db.add(rep)
    else:
        try:
            reports = json.loads(rep.reports_list)
        except Exception:
            reports = []
        reports.append(new_report)
        rep.reports_list = json.dumps(reports)
        rep.flag_count += 1
        rep.updated_at = datetime.utcnow()
        
    db.commit()
