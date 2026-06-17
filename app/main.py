from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from secrets import compare_digest

from models import AppointmentCreate, AppointmentUpdate, LoginRequest, TokenResponse

app = FastAPI(
    title="Clinic Appointment API",
    description="A simple API for managing clinic appointments.",
    version="2.0.0"
)

security = HTTPBearer()

appointments = {}
next_id = 1

USERS = {
    "admin": {"password": "clinic123", "token": "clinic-secret-token", "role": "clinic_staff"},
    "staff": {"password": "staff123", "token": "staff-secret-token", "role": "clinic_assistant"},
}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    for username, data in USERS.items():
        if compare_digest(token, data["token"]):
            return {"username": username, "role": data["role"]}
        
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing token"
    )

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Clinic Appointment API!",
        "version": "2.0.0",
        "authentication": "Bearer token required for appointment endpoints",
        "docs": "/docs"
    }

@app.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    for username, data in USERS.items():
        if compare_digest(login_data.username, username) and compare_digest(login_data.password, data["password"]):
            return {"access_token": data["token"], "token_type": "bearer", "role": data["role"]}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )

@app.get("/me")
def get_current_user(current_user: dict = Depends(verify_token)):
    return {
        "message": "Authenticated user",
        "user": current_user
    }   

@app.get("/appointments")
def get_appointments(current_user: dict = Depends(verify_token)):
    return {
        "count": len(appointments),
        "appointments": appointments
    }

@app.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: int, current_user: dict = Depends(verify_token)):
    if appointment_id not in appointments:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
    
        )
    return appointments[appointment_id]

@app.post("/appointments", status_code=status.HTTP_201_CREATED)
def create_appointment(appointment: AppointmentCreate, current_user: dict = Depends(verify_token)):
    global next_id;

    new_appointment = {
        "id": next_id,
        "patient_name": appointment.patient_name,
        "doctor_name": appointment.doctor_name,
        "appointment_date": appointment.appointment_date,
        "appointment_time": appointment.appointment_time,
        "reason": appointment.reason,
        "status": "scheduled",
        "created_by": current_user["username"]
    }

    appointments[next_id] = new_appointment
    next_id += 1

    return {
        "message": "Appointment created successfully",
        "appointment": new_appointment
    }

@app.put("/appointments/{appointment_id}")
def update_appointment(appointment_id: int, appointment_update: AppointmentUpdate, AppointmentUpdate, current_user: dict = Depends(verify_token)):
    if appointment_id not in appointments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    existing_appointment = appointments[appointment_id]
    update_data = appointment_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        existing_appointment[key] = value

    appointments[appointment_id] = existing_appointment

    existing_appointment["updated_by"] = current_user["username"]
    appointments[appointment_id] = existing_appointment

    return {
        "message": "Appointment updated successfully",
        "appointment": existing_appointment
    }

@app.delete("/appointments/{appointment_id}")
def cancel_appointment(appointment_id: int, current_user: dict = Depends(verify_token)):
    if current_user["role"] != "clinic_staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clinic staff may cancel appointments"
        )

    if appointment_id not in appointments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    appointments[appointment_id]["status"] = "cancelled"
    appointments[appointment_id]["cancelled_by"] = current_user["username"]

    return {
        "message": "Appointment cancelled successfully",
        "appointment": appointments[appointment_id]
    }


# @app.get("/health")
# def health_check():
#     return {"status": "API is running"}

# @app.get("/appointments/status/{status}")
# def get_appointments_by_status(status: str):
#     filtered = [
#         appointment for appointment in appointments.values()
#         if appointment["status"].lower() == status.lower()
#     ]
#     return {
#         "count": len(filtered),
#         "appointments": filtered
#     }

    
# @app.get("/appointments/doctor/{doctor_name}")
# def get_appointments_by_doctor(doctor_name: str):
#     filtered = [
#         appointment for appointment in appointments.values()
#         if appointment["doctor_name"].lower() == doctor_name.lower()
#     ]
#     return {
#         "count": len(filtered),
#         "appointments": filtered
#     }





