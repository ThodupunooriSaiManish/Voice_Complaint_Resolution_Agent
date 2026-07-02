import uuid
from datetime import datetime
from app.database import db
from app.subagents import check_ollama_status, rule_based_agent_mock
from app.subagents.extractor import extractor_agent
from app.subagents.analyzer import analyzer_agent
from app.subagents.planner import planner_agent

class AgentManager:
    def __init__(self):
        pass

    def process_transcript(self, transcript: str) -> dict:
        """
        Coordinates the execution of subagents synchronously to extract data, analyze sentiment,
        plan a resolution, store it in the database, and compile the final response.
        """
        print(f"\n[Agent Manager] Starting workflow for transcript: '{transcript[:100]}...'")
        
        # Check if Ollama is reachable
        ollama_reachable = check_ollama_status()
        
        ticket_data = {}
        
        if ollama_reachable:
            try:
                # 1. Run Extractor
                extraction = extractor_agent.extract(transcript)
                
                # 2. Run Analyzer
                analysis = analyzer_agent.analyze(transcript)
                
                # 3. Run Planner
                plan_data = planner_agent.plan(transcript, extraction, analysis)
                
                # Assemble
                ticket_data = {
                    "customer_name": extraction.get("customer_name"),
                    "contact_number": extraction.get("contact_number"),
                    "product_or_service": extraction.get("product_or_service"),
                    "complaint_description": extraction.get("complaint_description") or transcript,
                    "incident_date": extraction.get("incident_date"),
                    "sentiment": analysis.get("sentiment", "Neutral"),
                    "severity": analysis.get("severity", "Medium"),
                    "priority": analysis.get("priority", "P2"),
                    "resolution_plan": plan_data.get("resolution_plan", []),
                    "customer_response": plan_data.get("customer_response", "We have received your complaint.")
                }
            except Exception as e:
                print(f"[Agent Manager] Orchestration failed with error: {e}. Falling back to Rule-based mock.")
                ticket_data = rule_based_agent_mock(transcript)
        else:
            ticket_data = rule_based_agent_mock(transcript)

        # Ensure database structure fields
        ticket_data["id"] = str(uuid.uuid4())
        ticket_data["created_at"] = datetime.now().isoformat()
        
        # Save to database (MongoDB or JSON fallback)
        saved_ticket = db.save_ticket(ticket_data)
        print(f"[Agent Manager] Successfully generated and saved ticket: {saved_ticket['id']} under priority {saved_ticket['priority']}\n")
        
        return saved_ticket

agent_manager = AgentManager()
