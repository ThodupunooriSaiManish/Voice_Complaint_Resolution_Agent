import httpx
import json
import re
from app.config import settings

# Global client for connections (synchronous)
client = httpx.Client(timeout=30.0)

def check_ollama_status() -> bool:
    """
    Checks if the Ollama service is reachable.
    """
    try:
        response = client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            print(f"[Ollama] Reachable. Available models: {models}")
            return True
    except Exception as e:
        pass
    print(f"[Ollama] Unreachable at {settings.OLLAMA_BASE_URL}. Using high-quality Rule-based Mock Agent Fallbacks.")
    return False

def query_ollama(system_prompt: str, user_prompt: str, response_schema: dict = None) -> str:
    """
    Sends a query to Ollama's OpenAI-compatible endpoint.
    If response_schema is provided, requests JSON formatting.
    """
    url = f"{settings.OLLAMA_BASE_URL}/v1/chat/completions"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1
    }
    
    if response_schema:
        payload["response_format"] = {"type": "json_object"}
        
    try:
        response = client.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return content
        else:
            raise Exception(f"Ollama returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Ollama Error] Query failed: {e}")
        raise e

def clean_json_string(raw_str: str) -> str:
    """
    Cleans markdown code blocks out of JSON string if the model returned them.
    """
    cleaned = re.sub(r"```json\s*", "", raw_str)
    cleaned = re.sub(r"```\s*", "", cleaned)
    return cleaned.strip()

def rule_based_agent_mock(transcript: str) -> dict:
    """
    Generates a structured, high-quality, mock complaint ticket based on keywords in the transcript.
    This acts as a solid fallback when Ollama is unavailable.
    """
    name_match = re.search(r"name is ([A-Za-z]+ [A-Za-z]+|[A-Za-z]+)", transcript, re.IGNORECASE)
    customer_name = name_match.group(1) if name_match else "Valued Customer"
    
    phone_match = re.search(r"(\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{5,10}\b)", transcript)
    contact_number = phone_match.group(1) if phone_match else "Not Provided"

    product = "General Item"
    if "refrigerator" in transcript.lower() or "fridge" in transcript.lower():
        product = "Refrigerator / Freezer"
    elif "kettle" in transcript.lower():
        product = "Electric Kettle K300"
    elif "vacuum" in transcript.lower():
        product = "Vacuum Cleaner"
    elif "blender" in transcript.lower():
        product = "Blender"
    elif "water" in transcript.lower() or "leak" in transcript.lower():
        product = "Water Appliance"

    sentiment = "Neutral"
    if any(w in transcript.lower() for w in ["angry", "furious", "unacceptable", "terrible", "fire", "safety"]):
        sentiment = "Angry"
    elif any(w in transcript.lower() for w in ["frustrated", "wrong", "melted", "loud", "noise", "leak"]):
        sentiment = "Frustrated"

    severity = "Medium"
    priority = "P2"
    if "fire" in transcript.lower() or "spark" in transcript.lower() or "hazard" in transcript.lower() or "safety" in transcript.lower():
        severity = "Critical"
        priority = "P0"
    elif "not cooling" in transcript.lower() or "not freezing" in transcript.lower() or "melted" in transcript.lower() or "leak" in transcript.lower():
        severity = "High"
        priority = "P1"

    resolution_plan = [
        "Create replacement or repair order for the customer.",
        "Validate warranty status.",
        "Notify the support manager of customer frustration."
    ]
    if priority == "P0":
        resolution_plan.insert(0, "IMMEDIATE SAFETY ALERT: Escalate to safety response team.")
        resolution_plan.append("Initiate product recall check for model.")
        
    customer_response = f"Hello {customer_name}, I am truly sorry to hear about the issue with your {product}. I've logged a priority {priority} ticket for this complaint, and our support team is working on a resolution plan immediately. Thank you for reporting this."

    return {
        "customer_name": customer_name,
        "contact_number": contact_number,
        "product_or_service": product,
        "complaint_description": transcript,
        "incident_date": "Recently",
        "sentiment": sentiment,
        "severity": severity,
        "priority": priority,
        "resolution_plan": resolution_plan,
        "customer_response": customer_response
    }
