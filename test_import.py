import sys
import traceback

print("Testing imports...")
try:
    import gradio as gr
    print("✅ gradio imported successfully")
except ImportError:
    print("❌ gradio import failed")
    traceback.print_exc()

try:
    import requests
    print("✅ requests imported successfully")
except ImportError:
    print("❌ requests import failed")
    traceback.print_exc()

try:
    from dotenv import load_dotenv
    print("✅ dotenv imported successfully")
except ImportError:
    print("❌ dotenv import failed")
    traceback.print_exc()

print("-" * 20)
try:
    print("Importing database...")
    from database import add_patient, init_db
    print("✅ database imported successfully")
except Exception:
    print("❌ database import failed")
    traceback.print_exc()

print("-" * 20)

try:
    print("Importing calendar_service...")
    from calendar_service import CalendarService
    print("✅ calendar_service imported successfully")
except Exception:
    print("❌ calendar_service import failed")
    traceback.print_exc()
