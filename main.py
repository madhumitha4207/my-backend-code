from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from firebase_admin import auth, messaging
from auth import verify_firebase_token

app = FastAPI()

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class NotificationPayload(BaseModel):
    token: str  # The device FCM token from Flutter
    title: str
    body: str

# Route 1: Register User (Phase 1)
@app.post("/register")
def register_user(user: UserRegister):
    try:
        new_user = auth.create_user(
            email=user.email,
            password=user.password
        )
        return {"message": "User registered successfully", "uid": new_user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Route 2: Verify Token (Phase 2)
@app.get("/verify-user")
def verify_user(uid: str = Depends(verify_firebase_token)):
    return {
        "status": "success",
        "firebase_uid": uid,
        "message": "Token valid!"
    }

# Route 3: Send Push Notification (Phase 3)
@app.post("/send-notification")
def send_push_notification(payload: NotificationPayload, uid: str = Depends(verify_firebase_token)):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=payload.title,
                body=payload.body,
            ),
            token=payload.token,
        )
        response = messaging.send(message)
        return {
            "status": "success",
            "message_id": response,
            "sent_by_uid": uid
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to send notification: {str(e)}")


        # --- PHASE 4: Business Logic & Escalation Flow ---

from typing import Optional

class AlertPayload(BaseModel):
    elder_uid: str
    alert_type: str  # e.g., "MISSED_MEDICATION", "SOS_BUTTON", "ABNORMAL_ROUTINE"
    severity: str    # e.g., "LOW", "MEDIUM", "HIGH", "CRITICAL"
    message: str

@app.post("/trigger-alert")
def trigger_alert(payload: AlertPayload, uid: str = Depends(verify_firebase_token)):
    try:
        # 1. Log the alert (Database teammate can hook in here)
        
        # 2. Evaluate Escalation Flow based on severity
        escalation_status = "Direct Notification Sent"
        if payload.severity in ["HIGH", "CRITICAL"]:
            escalation_status = "Escalated to Caregiver (High/Critical Severity)"
            
        return {
            "status": "success",
            "alert_type": payload.alert_type,
            "severity": payload.severity,
            "escalation_action": escalation_status,
            "triggered_by": uid
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process alert: {str(e)}")