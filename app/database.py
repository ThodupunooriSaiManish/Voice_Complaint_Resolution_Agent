import json
import os
import uuid
from datetime import datetime
from typing import List, Dict
from app.config import settings

# Attempt to import pymongo for sync MongoDB connection
try:
    from pymongo import MongoClient
    from pymongo.errors import ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

class DatabaseManager:
    def __init__(self):
        self.use_fallback = True
        self.client = None
        self.db = None
        self.collection = None
        self.fallback_file = settings.DB_FALLBACK_PATH
        
        # Ensure fallback file directory exists
        fallback_dir = os.path.dirname(self.fallback_file)
        if fallback_dir:
            os.makedirs(fallback_dir, exist_ok=True)
            
        if not os.path.exists(self.fallback_file):
            with open(self.fallback_file, "w") as f:
                json.dump([], f)

    def connect(self):
        """
        Synchronous database connection for Streamlit.
        """
        if not PYMONGO_AVAILABLE:
            print("PyMongo not installed. Falling back to local JSON database.")
            self.use_fallback = True
            return
            
        try:
            print(f"Connecting to MongoDB at {settings.MONGO_URI}...")
            # Set a low timeout so we don't block Streamlit startup if Mongo is down
            self.client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
            self.db = self.client[settings.MONGO_DB]
            self.collection = self.db["tickets"]
            # Test connection
            self.client.server_info()
            self.use_fallback = False
            print("Successfully connected to MongoDB.")
        except Exception as e:
            print(f"MongoDB connection failed: {e}. Falling back to local JSON database.")
            self.use_fallback = True

    def save_ticket(self, ticket: Dict) -> Dict:
        ticket = dict(ticket)
        # Ensure timestamp and ID
        if "id" not in ticket:
            ticket["id"] = str(uuid.uuid4())
        if "created_at" not in ticket:
            ticket["created_at"] = datetime.now().isoformat()
            
        if not self.use_fallback and self.collection is not None:
            try:
                self.collection.insert_one(ticket)
                # Remove MongoDB _id from returned dict for serialization
                ticket.pop("_id", None)
                return ticket
            except Exception as e:
                print(f"MongoDB insert failed: {e}. Writing to fallback JSON.")
                
        # Fallback JSON saving
        self._save_fallback(ticket)
        return ticket

    def _save_fallback(self, ticket: Dict):
        try:
            data = []
            if os.path.exists(self.fallback_file):
                with open(self.fallback_file, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            data.insert(0, ticket) # Prepend
            with open(self.fallback_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to write to fallback database file: {e}")

    def get_all_tickets(self) -> List[Dict]:
        if not self.use_fallback and self.collection is not None:
            try:
                cursor = self.collection.find({}, {"_id": 0}).sort("created_at", -1)
                return list(cursor)
            except Exception as e:
                print(f"MongoDB query failed: {e}. Reading from fallback JSON.")
                
        # Fallback JSON reading
        return self._read_fallback()

    def _read_fallback(self) -> List[Dict]:
        try:
            if os.path.exists(self.fallback_file):
                with open(self.fallback_file, "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Failed to read from fallback database file: {e}")
            return []

    def delete_ticket(self, ticket_id: str) -> bool:
        if not self.use_fallback and self.collection is not None:
            try:
                result = self.collection.delete_one({"id": ticket_id})
                return result.deleted_count > 0
            except Exception as e:
                print(f"MongoDB delete failed: {e}. Deleting from fallback JSON.")
                
        # Fallback JSON deleting
        return self._delete_fallback(ticket_id)

    def _delete_fallback(self, ticket_id: str) -> bool:
        try:
            if not os.path.exists(self.fallback_file):
                return False
            with open(self.fallback_file, "r") as f:
                tickets = json.load(f)
            
            initial_len = len(tickets)
            tickets = [t for t in tickets if t.get("id") != ticket_id]
            
            if len(tickets) < initial_len:
                with open(self.fallback_file, "w") as f:
                    json.dump(tickets, f, indent=2)
                return True
            return False
        except Exception as e:
            print(f"Failed to delete from fallback database file: {e}")
            return False

db = DatabaseManager()
# Run initial connection
db.connect()
