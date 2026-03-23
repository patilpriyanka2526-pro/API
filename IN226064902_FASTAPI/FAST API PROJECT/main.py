
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional
import math

app = FastAPI()

# --- 1. DATA MODELS (Q6, Q9, Q11) ---

class AppointmentRequest(BaseModel):
    patient_name: str = Field(..., min_length=2)
    doctor_id: int = Field(..., gt=0)
    date: str = Field(..., min_length=8)
    reason: str = Field(..., min_length=5)
    appointment_type: str = "in-person"  # Default value
    senior_citizen: bool = False # Q9

class NewDoctor(BaseModel): # Q11
    name: str = Field(..., min_length=2)
    specialization: str = Field(..., min_length=2)
    fee: int = Field(..., gt=0)
    experience_years: int = Field(..., gt=0)
    is_available: bool = True

# --- 2. MOCK DATABASE ---

doctors = [
    {"id": 1, "name": "Dr. Smith", "specialization": "Cardiologist", "fee": 500, "experience_years": 12, "is_available": True},
    {"id": 2, "name": "Dr. Jones", "specialization": "Dermatologist", "fee": 300, "experience_years": 8, "is_available": True},
    {"id": 3, "name": "Dr. Taylor", "specialization": "Pediatrician", "fee": 250, "experience_years": 5, "is_available": False},
    {"id": 4, "name": "Dr. Brown", "specialization": "General", "fee": 200, "experience_years": 15, "is_available": True},
    {"id": 5, "name": "Dr. Wilson", "specialization": "Cardiologist", "fee": 600, "experience_years": 20, "is_available": True},
    {"id": 6, "name": "Dr. Miller", "specialization": "Pediatrician", "fee": 350, "experience_years": 3, "is_available": False},
]

appointments = []
appt_counter = 1

# --- 3. HELPER FUNCTIONS (Q7, Q9, Q10) ---

def find_doctor(doc_id: int):
    return next((d for d in doctors if d["id"] == doc_id), None)

def calculate_fee(base_fee: int, appt_type: str, is_senior: bool):
    # This is the starting price (e.g., 500)
    original_base = float(base_fee)
    
    # Calculate type multiplier
    type_clean = appt_type.lower()
    fee_after_type = original_base
    
    if type_clean == "video":
        fee_after_type = original_base * 0.8
    elif type_clean == "emergency":
        fee_after_type = original_base * 1.5
    
    # Apply senior discount to the result
    final_fee = fee_after_type
    if is_senior:
        final_fee = fee_after_type * 0.85
        
    # Return: (The doctor's base price, The final calculated price)
    return round(original_base, 2), round(final_fee, 2)

# --- 4. ENDPOINTS: DOCTORS (Q1, Q2, Q3, Q5, Q10-Q13, Q16-Q18, Q20) ---

@app.get("/")
def welcome():
    return {"message": "Welcome to MediCare Clinic"}

@app.get("/doctors/summary") # Q5
def get_summary():
    available = [d for d in doctors if d["is_available"]]
    return {
        "total": len(doctors),
        "available": len(available),
        "most_experienced": max(doctors, key=lambda x: x["experience_years"])["name"],
        "cheapest_fee": min(doctors, key=lambda x: x["fee"])["fee"],
        "by_specialty": {s: len([d for d in doctors if d["specialization"] == s]) for s in set(d["specialization"] for d in doctors)}
    }

@app.get("/doctors/filter") # Q10
def filter_doctors(
    specialization: Optional[str] = None, 
    max_fee: Optional[int] = None, 
    min_exp: Optional[int] = None, 
    available: Optional[bool] = None
):
    results = doctors
    if specialization: results = [d for d in results if d["specialization"].lower() == specialization.lower()]
    if max_fee: results = [d for d in results if d["fee"] <= max_fee]
    if min_exp: results = [d for d in results if d["experience_years"] >= min_exp]
    if available is not None: results = [d for d in results if d["is_available"] == available]
    return results

@app.get("/doctors/search") # Q16
def search_doctors(keyword: str):
    k = keyword.lower()
    results = [d for d in doctors if k in d["name"].lower() or k in d["specialization"].lower()]
    if not results: return {"message": f"No doctors found matching '{keyword}'"}
    return {"results": results, "total_found": len(results)}

@app.get("/doctors/sort") # Q17
def sort_doctors(sort_by: str = Query("fee", enum=["fee", "name", "experience_years"])):
    sorted_list = sorted(doctors, key=lambda x: x[sort_by])
    return {"sorted_by": sort_by, "data": sorted_list}

@app.get("/doctors/page") # Q18
def paginate_doctors(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    end = start + limit
    total_pages = math.ceil(len(doctors) / limit)
    return {"data": doctors[start:end], "page": page, "total_pages": total_pages}

@app.get("/doctors/browse") # Q20
def browse_doctors(keyword: Optional[str] = None, sort_by: str = "fee", order: str = "asc", page: int = 1, limit: int = 4):
    res = doctors
    if keyword:
        res = [d for d in res if keyword.lower() in d["name"].lower() or keyword.lower() in d["specialization"].lower()]
    
    res = sorted(res, key=lambda x: x[sort_by], reverse=(order == "desc"))
    
    start = (page - 1) * limit
    return {"results": res[start:start+limit], "metadata": {"total": len(res), "page": page, "limit": limit}}

@app.get("/doctors") # Q2
def get_doctors():
    return {"doctors": doctors, "total": len(doctors)}

@app.post("/doctors", status_code=201) # Q11
def add_doctor(doc: NewDoctor):
    if any(d["name"].lower() == doc.name.lower() for d in doctors):
        raise HTTPException(status_code=400, detail="Doctor name already exists")
    new_doc = doc.dict()
    new_doc["id"] = len(doctors) + 1
    doctors.append(new_doc)
    return new_doc

@app.get("/doctors/{doctor_id}") # Q3
def get_doctor(doctor_id: int):
    doc = find_doctor(doctor_id)
    if not doc: raise HTTPException(status_code=404, detail="Doctor not found")
    return doc

@app.put("/doctors/{doctor_id}") # Q12
def update_doctor(doctor_id: int, fee: Optional[int] = None, is_available: Optional[bool] = None):
    doc = find_doctor(doctor_id)
    if not doc: raise HTTPException(status_code=404, detail="Doctor not found")
    if fee is not None: doc["fee"] = fee
    if is_available is not None: doc["is_available"] = is_available
    return doc

@app.delete("/doctors/{doctor_id}") # Q13
def delete_doctor(doctor_id: int):
    doc = find_doctor(doctor_id)
    if not doc: raise HTTPException(status_code=404, detail="Doctor not found")
    if any(a["doctor_id"] == doctor_id and a["status"] == "scheduled" for a in appointments):
        raise HTTPException(status_code=400, detail="Cannot delete doctor with active appointments")
    doctors.remove(doc)
    return {"message": "Doctor deleted successfully"}

# --- 5. ENDPOINTS: APPOINTMENTS (Q4, Q6, Q8, Q14, Q15, Q19) ---

@app.post("/appointments") # Q8
def create_appointment(req: AppointmentRequest):
    global appt_counter
    doc = find_doctor(req.doctor_id)
    if not doc: raise HTTPException(status_code=404, detail="Doctor not found")
    if not doc["is_available"]: raise HTTPException(status_code=400, detail="Doctor is not available")
    
    orig_fee, final_fee = calculate_fee(doc["fee"], req.appointment_type, req.senior_citizen)
    
    new_appt = {
        "appointment_id": appt_counter,
        "patient": req.patient_name,
        "doctor_name": doc["name"],
        "doctor_id": doc["id"],
        "date": req.date,
        "type": req.appointment_type,
        "original_fee": orig_fee,
        "calculated_fee": final_fee,
        "status": "scheduled"
    }
    appointments.append(new_appt)
    appt_counter += 1
    return new_appt

@app.get("/appointments") # Q4
def get_all_appts():
    return {"appointments": appointments, "total": len(appointments)}

@app.get("/appointments/active") # Q15
def get_active_appts():
    return [a for a in appointments if a["status"] in ["scheduled", "confirmed"]]

@app.get("/appointments/search") # Q19
def search_appts(name: str):
    return [a for a in appointments if name.lower() in a["patient"].lower()]

@app.post("/appointments/{appt_id}/confirm") # Q14
def confirm_appt(appt_id: int):
    appt = next((a for a in appointments if a["appointment_id"] == appt_id), None)
    if not appt: raise HTTPException(status_code=404, detail="Appointment not found")
    appt["status"] = "confirmed"
    return appt

@app.post("/appointments/{appt_id}/cancel") # Q14
def cancel_appt(appt_id: int):
    appt = next((a for a in appointments if a["appointment_id"] == appt_id), None)
    if not appt: raise HTTPException(status_code=404, detail="Appointment not found")
    appt["status"] = "cancelled"
    doc = find_doctor(appt["doctor_id"])
    if doc: doc["is_available"] = True
    return appt

@app.post("/appointments/{appt_id}/complete") # Q15
def complete_appt(appt_id: int):
    appt = next((a for a in appointments if a["appointment_id"] == appt_id), None)
    if not appt: raise HTTPException(status_code=404, detail="Appointment not found")
    appt["status"] = "completed"
    return appt


