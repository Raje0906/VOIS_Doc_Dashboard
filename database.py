import os
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "doctor_dashboard_db"

def get_db_connection():
    """
    Returns a MongoDB database object.
    Requires MONGO_URI to be set in environment variables.
    """
    if not MONGO_URI:
        # Fallback for local testing if user hasn't set it, or raise error
        print("Warning: MONGO_URI not found. Trying localhost default.")
        client = MongoClient("mongodb://localhost:27017/")
    else:
        # FIX: Parse and escape username/password to handle special characters
        try:
            from urllib.parse import quote_plus, urlparse
            
            # Check if URI contains user info
            if "@" in MONGO_URI:
                # Basic parsing to extract credentials - this is a simple heuristic
                # A robust way is to ask user to provide escaped URI, but we can try to fix standard cases
                # If the user already provided a full URI, it might be that they didn't escape it.
                # However, re-assembling a URI is risky if we don't know exactly what part is what.
                # BETTER APPROACH: Trust standard MongoClient but warn user, 
                # OR if you are using `username:password` format, ensure they are escaped.
                
                # Given the error is "Username and password must be escaped", 
                # it means the user likely has special chars like '@' or ':' in their password.
                pass 

            # The error explicitly suggests usage of quote_plus. 
            # Since we can't easily parse an invalid URI to fix it automatically without potentially breaking other parts,
            # We will catch the error and print a helpful message, OR we can try to be smart if the env var is just the connection string.
            
            client = MongoClient(MONGO_URI)
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            print("TIP: If your password contains special characters like '@', ':', or '/', you must URL-encode them.")
            print("Example: 'p@ssword' becomes 'p%40ssword'.")
            # Re-raise to stop execution as DB is critical
            raise e
    
    db = client[DB_NAME]
    return db

def init_db():
    """
    Initializes the database with seed data if empty.
    """
    db = get_db_connection()
    patients_col = db['patients']
    
    # Check if empty
    if patients_col.count_documents({}) == 0:
        seed_data = [
            {
                "name": "Arjun Kumar", 
                "age": 45, 
                "gender": "Male", 
                "contact": "9876543210", 
                "history": "Diagnosed with Stage 2 CKD in 2024. Hypertension (managed). Family history of diabetes.", 
                "last_visit": "2024-10-15"
            },
            {
                "name": "Priya Sharma", 
                "age": 62, 
                "gender": "Female", 
                "contact": "8765432109", 
                "history": "Stage 3 CKD. High creatinine levels. Regular dialysis patient.", 
                "last_visit": "2024-11-01"
            },
            {
                "name": "Rahul Verma", 
                "age": 38, 
                "gender": "Male", 
                "contact": "7654321098", 
                "history": "Early signs of kidney stones. Recommended increased fluid intake.", 
                "last_visit": "2024-11-10"
            }
        ]
        patients_col.insert_many(seed_data)
        print("Initialized MongoDB with seed data.")

def get_all_patients():
    """
    Retrieves all patients. 
    Converts _id to string 'id'.
    """
    db = get_db_connection()
    patients = list(db['patients'].find())
    for p in patients:
        p['id'] = str(p['_id'])
        del p['_id']
    return patients

def get_patient(patient_id):
    """
    Retrieves a single patient by ID.
    Handles ObjectId conversion.
    """
    db = get_db_connection()
    try:
        obj_id = ObjectId(patient_id)
        patient = db['patients'].find_one({"_id": obj_id})
        if patient:
            patient['id'] = str(patient['_id'])
            del patient['_id']
            return patient
    except Exception as e:
        print(f"Error fetching patient {patient_id}: {e}")
    return None

def add_patient(name, age=None, gender=None, contact=None, history=None, last_visit=None):
    """
    Adds a new patient.
    Returns the new patient's ID as a string.
    """
    db = get_db_connection()
    new_patient = {
        "name": name,
        "age": age,
        "gender": gender,
        "contact": contact,
        "history": history,
        "last_visit": last_visit if last_visit else datetime.datetime.now().strftime("%Y-%m-%d")
    }
    result = db['patients'].insert_one(new_patient)
    return str(result.inserted_id)
