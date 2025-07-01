# SmartLeadAI

A FastAPI backend for multi-agent real estate lead qualification.

## Features
- Asks leads 5 qualification questions
- Stores answers in session (by phone number)
- Suggests a property from the agent's listings
- (Planned) Scores responses using Claude (OpenRouter)
- (Planned) Sends lead data to Make.com for Airtable/WhatsApp integration

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Mac/Linux
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API server:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### POST `/start_lead`
Start a new lead session.
```json
{
  "phone": "<phone_number>",
  "agent_id": "agent_ravi"
}
```

### POST `/answer`
Submit an answer and get the next question or lead result.
```json
{
  "phone": "<phone_number>",
  "answer": "My answer"
}
```

---

## Next Steps
- Integrate Claude (OpenRouter) for scoring
- Send data to Make.com webhook
- Add WhatsApp/web integration 