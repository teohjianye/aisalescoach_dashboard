#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime, timedelta
import random
import uuid

def init_database():
    conn = sqlite3.connect('../lib/database/sales_coaching.db')
    
    # Create tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS call_records (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            duration INTEGER,
            sales_rep_name TEXT,
            customer_name TEXT,
            audio_file_path TEXT,
            transcription TEXT,
            conversation TEXT,
            status TEXT,
            call_type TEXT,
            outcome TEXT,
            notes TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS call_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT,
            what_went_well TEXT,
            what_could_be_improved TEXT,
            discovery_questions_assessment TEXT,
            objection_handling_evaluation TEXT,
            customer_primary_concern TEXT,
            overall_score REAL,
            recommendations TEXT,
            conversation_metrics TEXT,
            feedback_timestamps TEXT,
            UNIQUE(call_id)
        )
    ''')
    
    # Sample data
    sales_reps = ["John Smith", "Sarah Johnson", "Mike Chen", "Emily Davis", "Alex Rodriguez"]
    call_types = ["Phone Call", "Google Meet", "Microsoft Teams", "Zoom", "In-person"]
    outcomes = ["Won", "Follow up required", "Lost", "Escalated"]
    customers = [
        "ABC Corp", "XYZ Industries", "Tech Solutions Inc", "Global Dynamics", "Innovation Labs",
        "Future Systems", "Prime Enterprises", "Digital Ventures", "Smart Solutions", "Elite Corp"
    ]
    
    # Generate sample call records with feedback
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(50):  # Generate 50 sample calls
        call_id = str(uuid.uuid4())
        timestamp = (base_date + timedelta(days=random.randint(0, 30), 
                                         hours=random.randint(8, 18), 
                                         minutes=random.randint(0, 59))).isoformat()
        duration = random.randint(300, 3600)  # 5 minutes to 1 hour
        sales_rep = random.choice(sales_reps)
        customer = random.choice(customers)
        call_type = random.choice(call_types)
        outcome = random.choice(outcomes)
        status = "completed"
        
        # Sample conversation
        conversation = [
            {
                "speaker": "sales_rep",
                "text": f"Hi {customer.split()[0]}, thank you for taking the time to speak with me today.",
                "startTime": 0.0,
                "endTime": 3.5,
                "confidence": 0.95,
                "notes": None
            },
            {
                "speaker": "customer",
                "text": "Thanks for reaching out. I'm interested in learning more about your solutions.",
                "startTime": 4.0,
                "endTime": 8.2,
                "confidence": 0.92,
                "notes": None
            },
            {
                "speaker": "sales_rep",
                "text": "Great! Let me start by understanding your current challenges and needs.",
                "startTime": 9.0,
                "endTime": 13.1,
                "confidence": 0.94,
                "notes": None
            }
        ]
        
        transcription = " ".join([turn["text"] for turn in conversation])
        
        # Insert call record
        conn.execute('''
            INSERT OR REPLACE INTO call_records 
            (id, timestamp, duration, sales_rep_name, customer_name, 
             audio_file_path, transcription, conversation, status, call_type, outcome, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (call_id, timestamp, duration, sales_rep, customer,
              f'/audio/{call_id}.wav', transcription, json.dumps(conversation),
              status, call_type, outcome, f"Call with {customer} via {call_type}"))
        
        # Generate realistic feedback scores based on call type and outcome
        base_score = 7.0
        if outcome == "Won":
            base_score = random.uniform(8.0, 9.5)
        elif outcome == "Follow up required":
            base_score = random.uniform(6.5, 8.0)
        elif outcome == "Lost":
            base_score = random.uniform(4.0, 6.5)
        elif outcome == "Escalated":
            base_score = random.uniform(5.0, 7.0)
        
        # Call type bonuses/penalties
        if call_type == "In-person":
            base_score += random.uniform(0.2, 0.8)
        elif call_type in ["Google Meet", "Microsoft Teams", "Zoom"]:
            base_score += random.uniform(0.1, 0.4)
        
        overall_score = min(10.0, max(1.0, base_score + random.uniform(-0.5, 0.5)))
        
        # Sample feedback
        what_went_well = [
            "Excellent rapport building with the customer",
            "Clear articulation of value proposition",
            "Good active listening throughout the call",
            "Effective use of discovery questions",
            "Professional handling of objections"
        ]
        
        what_could_be_improved = [
            "Could have asked more qualifying questions",
            "Missed opportunity to create urgency",
            "Could have better addressed pricing concerns",
            "Should have summarized next steps more clearly",
            "Could have probed deeper into pain points"
        ]
        
        conversation_metrics = {
            "talk_time_ratio": random.uniform(0.3, 0.7),
            "question_count": random.randint(3, 12),
            "objection_count": random.randint(0, 4),
            "closing_attempts": random.randint(1, 3),
            "engagement_score": random.uniform(6.0, 9.5)
        }
        
        recommendations = [
            "Focus on asking more open-ended discovery questions",
            "Practice objection handling techniques",
            "Work on creating urgency without being pushy",
            "Improve follow-up scheduling",
            "Enhance value proposition delivery"
        ]
        
        # Insert feedback
        conn.execute('''
            INSERT OR REPLACE INTO call_feedback 
            (call_id, what_went_well, what_could_be_improved, 
             discovery_questions_assessment, objection_handling_evaluation,
             customer_primary_concern, overall_score, recommendations, 
             conversation_metrics, feedback_timestamps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (call_id, 
              random.choice(what_went_well),
              random.choice(what_could_be_improved),
              f"Discovery questions were {'effective' if overall_score > 7 else 'adequate' if overall_score > 5 else 'needs improvement'}",
              f"Objection handling was {'strong' if overall_score > 7 else 'satisfactory' if overall_score > 5 else 'requires development'}",
              "Budget constraints and timeline concerns",
              overall_score,
              json.dumps(random.sample(recommendations, 3)),
              json.dumps(conversation_metrics),
              json.dumps({"generated_at": datetime.now().isoformat()})))
    
    conn.commit()
    conn.close()
    print("Database initialized with sample data!")
    print("Generated 50 sample call records with feedback")

if __name__ == "__main__":
    init_database() 