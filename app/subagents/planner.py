import json
from app.subagents import query_ollama, clean_json_string

class ComplaintPlanner:
    def __init__(self):
        self.system_prompt = (
            "You are an AI Sub-Agent specializing in Ticket and Customer Resolution Planning.\n"
            "Your task is to devise an action plan for resolving a customer's complaint and write a spoken response.\n"
            "You will be given the original transcript, customer details, and the assigned priority/sentiment.\n\n"
            "Generate:\n"
            "- resolution_plan: An array of strings containing step-by-step instructions for our human operations team.\n"
            "- customer_response: A highly professional, short (2-3 sentences), empathetic spoken script to read back to the customer. Maintain a friendly and reassuring tone.\n\n"
            "You MUST output raw JSON matching this schema exactly:\n"
            "{\n"
            "  \"resolution_plan\": [string, ...],\n"
            "  \"customer_response\": string\n"
            "}\n"
            "Provide ONLY the raw JSON output. No other conversational text or markdown blocks."
        )

    def plan(self, transcript: str, extraction: dict, analysis: dict) -> dict:
        print("[Planner Agent] Devising resolution plan and customer response...")
        context = {
            "transcript": transcript,
            "extracted_data": extraction,
            "analysis_data": analysis
        }
        user_prompt = f"Complaint Context:\n{json.dumps(context, indent=2)}"
        
        try:
            raw_response = query_ollama(self.system_prompt, user_prompt, response_schema=True)
            cleaned = clean_json_string(raw_response)
            data = json.loads(cleaned)
            print(f"[Planner Agent] Output: {data}")
            return data
        except Exception as e:
            print(f"[Planner Agent] Failed to query Ollama: {e}. Falling back to default plan.")
            name = extraction.get("customer_name") or "there"
            product = extraction.get("product_or_service") or "item"
            priority = analysis.get("priority", "P2")
            
            return {
                "resolution_plan": [
                    "Flag ticket for review by operations team.",
                    "Verify transaction or order records.",
                    "Arrange contact callback with supervisor."
                ],
                "customer_response": f"Hello, thank you for contacting us. I have registered your complaint regarding the {product} under priority {priority}. Our support team will inspect the details and follow up with you as soon as possible."
            }

planner_agent = ComplaintPlanner()
