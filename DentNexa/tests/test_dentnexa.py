import os
import sys
import unittest
from datetime import datetime

# Add src to python path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from shared.models import Patient, Dentist, Appointment
from shared import db as shared_db
from shared import rag as shared_rag
from app.whatsapp import format_message_content


class TestDentNexaFullSystem(unittest.TestCase):
    """Full Integration & Unit Test Suite for DentNexa Enterprise Agent."""

    @classmethod
    def setUpClass(cls):
        print("\n🧪 Initializing DentNexa Test Suite...")
        shared_db.init_db(seed=True)

    def test_01_database_initialization_and_dentists(self):
        """Tests DB init and default seeded dentists."""
        dentists = shared_db.get_all_dentists()
        self.assertGreaterEqual(len(dentists), 1, "Dentists list should not be empty")
        print(f"✅ DB Test Passed: Found {len(dentists)} dentists in DB.")

    def test_02_patient_creation_and_retrieval(self):
        """Tests creating a patient and retrieving by phone."""
        test_phone = "+966599999999"
        p = shared_db.create_patient(Patient(name="اختبار مريض", age=25, gender="Male", phone_number=test_phone))
        self.assertIsNotNone(p.id)
        
        retrieved = shared_db.get_patient_by_phone(test_phone)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "اختبار مريض")
        print("✅ Patient Query Test Passed: Patient created and retrieved successfully.")

    def test_03_appointment_booking_and_reminder_queries(self):
        """Tests appointment creation, status update, and reminder query."""
        test_phone = "+966599999999"
        patient = shared_db.get_patient_by_phone(test_phone)
        dentist = shared_db.get_all_dentists()[0]
        
        appt_time = datetime.now()
        appt = shared_db.create_appointment(Appointment(
            patient_id=patient.id,
            dentist_id=dentist.id,
            appointment_time=appt_time,
            status="scheduled"
        ))
        self.assertIsNotNone(appt.id)

        # Check reminder query
        upcoming = shared_db.get_upcoming_unreminded_appointments(hours_ahead=24)
        self.assertTrue(any(a["appointment_id"] == appt.id for a in upcoming))
        
        # Mark reminder sent
        marked = shared_db.mark_appointment_reminder_sent(appt.id)
        self.assertTrue(marked)
        print("✅ Appointment & Reminder Query Test Passed.")

    def test_04_rag_knowledge_base_search(self):
        """Tests RAG Knowledge Base search and match retrieval."""
        res = shared_rag.search_knowledge_base("تبييض الأسنان والأسعار")
        self.assertIn("matches", res)
        self.assertGreaterEqual(len(res["matches"]), 1)
        print("✅ RAG Search Test Passed: Retrieved knowledge base matches successfully.")

    def test_05_whatsapp_formatting(self):
        """Tests WhatsApp Markdown message formatting."""
        raw_text = "مرحباً **عبدالله**! 【تأكيد الموعد】"
        formatted = format_message_content(raw_text)
        self.assertNotIn("【", formatted)
        self.assertIn("*عبدالله*", formatted)
        print("✅ WhatsApp Formatting Test Passed.")

    def test_06_mcp_server_tools_import(self):
        """Tests importing MCP server module and tools registration."""
        from dentnexa_mcp.server import mcp, search_knowledge_base, get_current_time
        self.assertEqual(mcp.name, "dentnexa-mcp")
        self.assertIsNotNone(get_current_time())
        print("✅ MCP Server Module & Tools Test Passed.")


if __name__ == "__main__":
    unittest.main()
