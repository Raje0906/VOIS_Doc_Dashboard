from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from dotenv import load_dotenv
load_dotenv()
from rag_service import RAGService
from pdf_service import PDFReportGenerator
from calendar_service import CalendarService

app = Flask(__name__)

# Initialize Services
rag_service = RAGService()
pdf_generator = PDFReportGenerator()
calendar_service = CalendarService() # Will print warning if credentials missing

from database import init_db, get_all_patients, get_patient

app = Flask(__name__)

# Initialize Services
rag_service = RAGService()
pdf_generator = PDFReportGenerator()
calendar_service = CalendarService() # Will print warning if credentials missing

# Initialize DB
try:
    init_db()
except Exception as e:
    print(f"Error initializing DB: {e}")

@app.route('/')
def index():
    return render_template('doctor_dashboard.html')

@app.route('/api/patients', methods=['GET'])
def get_patients_route():
    return jsonify(get_all_patients())

@app.route('/api/patients/<patient_id>/history', methods=['GET'])
def get_patient_history(patient_id):
    patient = get_patient(patient_id)
    if patient:
        return jsonify(patient)
    return jsonify({"error": "Patient not found"}), 404

@app.route('/api/rag/query', methods=['POST'])
def query_rag():
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({"error": "Message required"}), 400
    
    response = rag_service.query_agent(message)
    return jsonify({"response": response})

@app.route('/api/medicine/recommend', methods=['POST'])
def recommend_medicine():
    data = request.json
    condition = data.get('condition')
    if not condition:
        return jsonify({"error": "Condition required"}), 400

    recommendations = rag_service.get_medicine_recommendations(condition)
    return jsonify({"recommendations": recommendations})

@app.route('/api/medicine/generate_pdf', methods=['POST'])
def generate_medicine_pdf():
    data = request.json
    condition = data.get('condition')
    recommendation = data.get('recommendation')
    
    if not condition or not recommendation:
        return jsonify({"error": "Condition and recommendation required"}), 400

    try:
        pdf_path = pdf_generator.generate_medicine_report(condition, recommendation)
        
        # Return relative path for frontend to download
        relative_path = os.path.relpath(pdf_path, start=os.getcwd())
        web_path = relative_path.replace(os.sep, '/')
        return jsonify({"pdf_url": '/' + web_path})
    except Exception as e:
        print(f"PDF Gen Error: {e}")
        return jsonify({"error": "Failed to generate PDF"}), 500

@app.route('/static/reports/<path:filename>')
def serve_report(filename):
    return send_from_directory('static/reports', filename)




@app.route('/api/calendar/events', methods=['GET'])
def get_events():
    try:
        events = calendar_service.get_upcoming_events()
        return jsonify(events)
    except Exception as e:
         return jsonify({"error": str(e)}), 500

@app.route('/api/calendar/slots', methods=['GET'])
def get_slots():
    # Helper to determine caller or just return available for patients
    # But now we might want to distinguish.
    # Patient app uses this. It expects a list of STRINGS (available times).
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"error": "Date required"}), 400
    try:
        slots = calendar_service.get_available_slots(date_str)
        return jsonify(slots)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/calendar/manage/status', methods=['GET'])
def get_manageable_slots():
    # For Doctor Dashboard
    date_str = request.args.get('date')
    if not date_str: return jsonify({"error": "Date required"}), 400
    try:
        status_map = calendar_service.get_slot_status(date_str)
        return jsonify(status_map)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/calendar/manage/toggle', methods=['POST'])
def toggle_slot():
    data = request.json
    date_str = data.get('date')
    time_str = data.get('time')
    action = data.get('action') # 'block' or 'unblock'
    
    if not all([date_str, time_str, action]):
        return jsonify({"error": "Missing fields"}), 400
        
    success, msg = calendar_service.toggle_slot(date_str, time_str, action)
    if success:
        return jsonify({"status": "success", "message": msg})
    else:
        return jsonify({"status": "error", "message": msg}), 500

@app.route('/api/calendar/book', methods=['POST'])
def book_appointment():
    data = request.json
    start_time = data.get('start_time') # e.g., '2024-11-20T10:00:00'
    summary = data.get('summary', 'Patient Appointment')
    
    if not start_time:
         return jsonify({"error": "Start time required"}), 400

    success, result = calendar_service.book_slot(start_time, summary=summary)
    
    if success:
        return jsonify({"status": "success", "link": result})
    else:
        return jsonify({"status": "error", "message": result}), 500

if __name__ == '__main__':
    print("Starting Doctor Dashboard on http://localhost:5000")
    app.run(debug=True, port=5000)
