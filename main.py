import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SmartLeadAI")

# In-memory session storage (keyed by phone number)
SESSIONS: Dict[str, Dict] = {}

# Static agent property listings
AGENT_PROPERTIES = {
    "agent_ravi": [
        {"title": "2BHK in Gachibowli", "price": "₹55L", "location": "Gachibowli"},
        {"title": "3BHK in Kondapur", "price": "₹78L", "location": "Kondapur"}
    ],
    "agent_sara": [
        {"title": "Villa in Jubilee Hills", "price": "₹1.2Cr", "location": "Jubilee Hills"}
    ]
}

# The 5 qualification questions
QUESTIONS = [
    "What type of property are you looking for? (e.g., 2BHK, Plot)",
    "What is your budget?",
    "Which location do you prefer?",
    "When do you plan to buy? (Immediately, 1 month, etc.)",
    "Are you ready with financing or a loan?"
]

class LeadInit(BaseModel):
    phone: str
    agent_id: str

class LeadResponse(BaseModel):
    phone: str
    answer: str

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

@app.post("/start_lead")
def start_lead(lead: LeadInit):
    """Initialize a new lead session."""
    if lead.phone in SESSIONS:
        return {"message": "Session already exists.", "question": QUESTIONS[SESSIONS[lead.phone]['current_q']]}    
    SESSIONS[lead.phone] = {
        "agent_id": lead.agent_id,
        "answers": [],
        "current_q": 0
    }
    return {"message": "Session started.", "question": QUESTIONS[0]}

@app.post("/answer")
def answer_lead(resp: LeadResponse):
    """Accept an answer from the lead and return the next question or process the lead."""
    session = SESSIONS.get(resp.phone)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Start with /start_lead.")
    session["answers"].append(resp.answer)
    session["current_q"] += 1
    if session["current_q"] < len(QUESTIONS):
        return {"message": "Next question.", "question": QUESTIONS[session["current_q"]]}
    # All questions answered, process lead
    agent_id = session["agent_id"]
    properties = AGENT_PROPERTIES.get(agent_id, [])
    answers = session["answers"]
    prompt = f"""
You are a real estate lead qualification agent.\n\nBased on the answers below, return:\n\nscore (0–100)\nstatus: Hot / Warm / Cold\nreason\nbest_match: pick the best property from agent's listings\n\nAnswers:\nProperty: {answers[0]}\nBudget: {answers[1]}\nLocation: {answers[2]}\nTimeline: {answers[3]}\nFinancing: {answers[4]}\n\nAgent Listings:\n{properties}\n\nRespond in JSON:\n{{\n\"score\": 82,\n\"status\": \"Hot\",\n\"reason\": \"Urgent buyer, ready with funds\",\n\"best_match\": \"2BHK in Gachibowli for ₹55L\"\n}}"""
    # Call Claude (OpenRouter API)
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        resp_ai = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers, timeout=30)
        resp_ai.raise_for_status()
        ai_content = resp_ai.json()["choices"][0]["message"]["content"]
    except Exception as e:
        ai_content = str(e)
    # Try to parse JSON from AI response
    import json
    try:
        result = json.loads(ai_content)
    except Exception:
        result = {"error": "AI response not valid JSON", "raw": ai_content}
    # Send to n8n webhook
    if MAKE_WEBHOOK_URL:
        try:
            requests.post(MAKE_WEBHOOK_URL, json={
                "phone": resp.phone,
                "agent_id": agent_id,
                "answers": answers,
                "ai_result": result,
                "properties": properties
            }, timeout=10)
        except Exception:
            pass
    del SESSIONS[resp.phone]
    return {"message": "Lead processed.", "ai_result": result, "properties": properties} 