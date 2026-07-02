import json
from app.subagents import query_ollama, clean_json_string

class ComplaintAnalyzer:
    def __init__(self):
        self.system_prompt = (
            "You are an AI Sub-Agent specializing in Complaint Sentiment & Severity Assessment.\n"
            "Analyze the customer's text transcript to evaluate:\n"
            "- sentiment: Must be one of ['Calm', 'Neutral', 'Frustrated', 'Angry']\n"
            "- severity: Must be one of ['Low', 'Medium', 'High', 'Critical']\n"
            "- priority: Must be one of ['P3', 'P2', 'P1', 'P0'] based on severity and sentiment. (P0 is immediate critical attention/hazards, P1 is high priority, P2 is medium, P3 is low)\n\n"
            "Guidelines:\n"
            "- If the transcript indicates safety hazards, fire, spark, or severe flooding, classify severity as 'Critical' and priority as 'P0'.\n"
            "- If the customer uses words like 'furious', 'horrible', 'demand refund', classify sentiment as 'Angry' or 'Frustrated'.\n\n"
            "You MUST output raw JSON matching this schema exactly:\n"
            "{\n"
            "  \"sentiment\": \"Calm\" | \"Neutral\" | \"Frustrated\" | \"Angry\",\n"
            "  \"severity\": \"Low\" | \"Medium\" | \"High\" | \"Critical\",\n"
            "  \"priority\": \"P3\" | \"P2\" | \"P1\" | \"P0\"\n"
            "}\n"
            "Provide ONLY the raw JSON output. No explanations, markdown tags, or extra text."
        )

    def analyze(self, transcript: str) -> dict:
        print("[Analyzer Agent] Assessing sentiment and severity...")
        user_prompt = f"Transcript to analyze:\n<user_transcript>\n{transcript}\n</user_transcript>"
        
        try:
            raw_response = query_ollama(self.system_prompt, user_prompt, response_schema=True)
            cleaned = clean_json_string(raw_response)
            data = json.loads(cleaned)
            print(f"[Analyzer Agent] Output: {data}")
            return data
        except Exception as e:
            print(f"[Analyzer Agent] Failed to query Ollama: {e}. Falling back to default assessment.")
            return {
                "sentiment": "Neutral",
                "severity": "Medium",
                "priority": "P2"
            }

analyzer_agent = ComplaintAnalyzer()
