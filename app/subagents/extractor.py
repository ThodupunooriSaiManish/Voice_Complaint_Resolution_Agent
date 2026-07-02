import json
from app.subagents import query_ollama, clean_json_string

class ComplaintExtractor:
    def __init__(self):
        self.system_prompt = (
            "You are an AI Sub-Agent specializing in Customer Complaint Information Extraction.\n"
            "Your task is to parse a raw text transcript of a voice message and extract structured details.\n"
            "Extract the following fields:\n"
            "- customer_name: Name of the caller (null if not mentioned)\n"
            "- contact_number: Phone number, order ID, or email (null if not mentioned)\n"
            "- product_or_service: The product or service the complaint is about (null if not mentioned)\n"
            "- complaint_description: A concise summary of the issue reported\n"
            "- incident_date: Date or time of the incident (null if not mentioned)\n\n"
            "You MUST output raw JSON matching this schema exactly:\n"
            "{\n"
            "  \"customer_name\": string or null,\n"
            "  \"contact_number\": string or null,\n"
            "  \"product_or_service\": string or null,\n"
            "  \"complaint_description\": string,\n"
            "  \"incident_date\": string or null\n"
            "}\n"
            "Provide ONLY the raw JSON output. No other text, explanations, or markdown code blocks."
        )

    def extract(self, transcript: str) -> dict:
        print("[Extractor Agent] Extracting info from transcript...")
        user_prompt = f"Transcript to parse:\n<user_transcript>\n{transcript}\n</user_transcript>"
        
        try:
            raw_response = query_ollama(self.system_prompt, user_prompt, response_schema=True)
            cleaned = clean_json_string(raw_response)
            data = json.loads(cleaned)
            print(f"[Extractor Agent] Output: {data}")
            return data
        except Exception as e:
            print(f"[Extractor Agent] Failed to query Ollama: {e}. Falling back to default extraction.")
            return {
                "customer_name": None,
                "contact_number": None,
                "product_or_service": None,
                "complaint_description": transcript,
                "incident_date": None
            }

extractor_agent = ComplaintExtractor()
