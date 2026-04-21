"""
Create a simple ADK-style agent like basic-gcp-agent-working
Relies purely on Cloud Logging capture (no direct Lambda forwarding)
"""
import vertexai
from vertexai.preview import reasoning_engines
from datetime import datetime
from typing import Dict, Any, List, Optional

PROJECT_ID = "agentic-ai-integration-490716"
LOCATION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"

print("=" * 60)
print("Creating Simple ADK Agent (Cloud Logging Only)")
print("=" * 60)
print(f"Project: {PROJECT_ID}")
print()

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)


class SimpleADKAgent:
    """
    Simple ADK-style agent like basic-gcp-agent-working
    No direct Lambda forwarding - relies on Cloud Logging capture
    """

    def __init__(self):
        self.project_id = PROJECT_ID
        self.sessions = {}  # In-memory session storage
        self.memories = {}  # In-memory user memories

    def create_session(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session for a user"""
        if session_id is None:
            session_id = f"session-{datetime.utcnow().timestamp()}"

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "messages": [],
            "state": {}
        }

        if user_id not in self.sessions:
            self.sessions[user_id] = {}

        self.sessions[user_id][session_id] = session
        print(f"[AGENT] Created session: {session_id} for user: {user_id}")

        return session

    def get_session(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get an existing session"""
        return self.sessions.get(user_id, {}).get(session_id)

    def add_to_memory(self, user_id: str, key: str, value: Any):
        """Add information to user memory"""
        if user_id not in self.memories:
            self.memories[user_id] = {}

        self.memories[user_id][key] = value
        print(f"[AGENT] Added to memory for {user_id}: {key} = {value}")

    def get_memory(self, user_id: str) -> Dict[str, Any]:
        """Get user memory"""
        return self.memories.get(user_id, {})

    def get_temperature(self, city: str) -> Dict[str, Any]:
        """
        Get temperature for a city (simulated data)
        In production, this would call a weather API
        """
        print(f"[TOOL] get_temperature called for: {city}")

        # Simulated temperature data
        temp_data = {
            "london": {"temp_c": 15, "temp_f": 59, "condition": "Cloudy"},
            "new york": {"temp_c": 22, "temp_f": 72, "condition": "Sunny"},
            "tokyo": {"temp_c": 18, "temp_f": 64, "condition": "Rainy"},
            "paris": {"temp_c": 17, "temp_f": 63, "condition": "Partly Cloudy"},
            "mumbai": {"temp_c": 32, "temp_f": 90, "condition": "Hot and Humid"},
            "sydney": {"temp_c": 20, "temp_f": 68, "condition": "Clear"}
        }

        city_lower = city.lower()
        if city_lower in temp_data:
            result = {
                "city": city,
                "temperature_celsius": temp_data[city_lower]["temp_c"],
                "temperature_fahrenheit": temp_data[city_lower]["temp_f"],
                "condition": temp_data[city_lower]["condition"],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            result = {
                "city": city,
                "temperature_celsius": 20,
                "temperature_fahrenheit": 68,
                "condition": "Data not available",
                "timestamp": datetime.utcnow().isoformat()
            }

        print(f"[TOOL] Temperature result: {result}")
        return result

    def get_location_info(self, city: str) -> Dict[str, Any]:
        """
        Get location information including country and coordinates
        In production, this would call a geocoding API
        """
        print(f"[TOOL] get_location_info called for: {city}")

        # Simulated location data
        location_data = {
            "london": {
                "country": "United Kingdom",
                "continent": "Europe",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "population": "9 million"
            },
            "new york": {
                "country": "United States",
                "continent": "North America",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "population": "8.3 million"
            },
            "tokyo": {
                "country": "Japan",
                "continent": "Asia",
                "latitude": 35.6762,
                "longitude": 139.6503,
                "population": "14 million"
            },
            "paris": {
                "country": "France",
                "continent": "Europe",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "population": "2.2 million"
            },
            "mumbai": {
                "country": "India",
                "continent": "Asia",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "population": "20 million"
            },
            "sydney": {
                "country": "Australia",
                "continent": "Oceania",
                "latitude": -33.8688,
                "longitude": 151.2093,
                "population": "5.3 million"
            }
        }

        city_lower = city.lower()
        if city_lower in location_data:
            result = {
                "city": city,
                **location_data[city_lower],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            result = {
                "city": city,
                "country": "Unknown",
                "continent": "Unknown",
                "latitude": 0.0,
                "longitude": 0.0,
                "population": "Unknown",
                "timestamp": datetime.utcnow().isoformat()
            }

        print(f"[TOOL] Location result: {result}")
        return result

    def get_capital(self, country: str) -> Dict[str, Any]:
        """
        Get capital city of a country
        In production, this would call a geography API
        """
        print(f"[TOOL] get_capital called for: {country}")

        # Simulated capital data
        capital_data = {
            "united kingdom": {"capital": "London", "language": "English"},
            "uk": {"capital": "London", "language": "English"},
            "united states": {"capital": "Washington D.C.", "language": "English"},
            "usa": {"capital": "Washington D.C.", "language": "English"},
            "japan": {"capital": "Tokyo", "language": "Japanese"},
            "france": {"capital": "Paris", "language": "French"},
            "india": {"capital": "New Delhi", "language": "Hindi, English"},
            "australia": {"capital": "Canberra", "language": "English"},
            "germany": {"capital": "Berlin", "language": "German"},
            "china": {"capital": "Beijing", "language": "Mandarin"},
            "brazil": {"capital": "Brasília", "language": "Portuguese"},
            "canada": {"capital": "Ottawa", "language": "English, French"}
        }

        country_lower = country.lower()
        if country_lower in capital_data:
            result = {
                "country": country,
                "capital": capital_data[country_lower]["capital"],
                "official_language": capital_data[country_lower]["language"],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            result = {
                "country": country,
                "capital": "Unknown",
                "official_language": "Unknown",
                "timestamp": datetime.utcnow().isoformat()
            }

        print(f"[TOOL] Capital result: {result}")
        return result

    def analyze_message(self, message_data: str, user_id: str) -> Dict[str, Any]:
        """Analyze message with context from user memory"""
        print(f"[AGENT] Analyzing message for user: {user_id}")

        # Get user context from memory
        user_memory = self.get_memory(user_id)

        analysis = {
            "severity": "INFO",
            "category": "info",
            "anomaly_detected": False,
            "insights": "Normal monitoring data",
            "timestamp": datetime.utcnow().isoformat(),
            "user_context": user_memory
        }

        message_lower = message_data.lower()

        if any(kw in message_lower for kw in ['error', 'exception', 'failed', 'critical']):
            analysis.update({
                "severity": "HIGH",
                "category": "error",
                "anomaly_detected": True,
                "insights": "Error detected - immediate attention required"
            })

            # Update memory with error count
            error_count = user_memory.get("error_count", 0) + 1
            self.add_to_memory(user_id, "error_count", error_count)
            self.add_to_memory(user_id, "last_error", message_data[:100])
            print(f"[AGENT] ERROR DETECTED - User {user_id} error count: {error_count}")

        elif any(kw in message_lower for kw in ['warning', 'warn']):
            analysis.update({
                "severity": "MEDIUM",
                "category": "warning",
                "insights": "Warning detected"
            })
            print(f"[AGENT] WARNING DETECTED")

        print(f"[AGENT] Analysis complete: {analysis['severity']} - {analysis['insights']}")
        return analysis

    def stream_query(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process query with streaming-style response
        Like basic-gcp-agent-working - logs automatically captured by Cloud Logging
        """
        print(f"[{datetime.utcnow().isoformat()}] === Stream Query Start ===")
        print(f"[AGENT] User: {user_id}, Session: {session_id}")
        print(f"[AGENT] Message: {message}")

        # Get or create session
        if session_id:
            session = self.get_session(user_id, session_id)
            if not session:
                session = self.create_session(user_id, session_id)
        else:
            session = self.create_session(user_id)
            session_id = session["session_id"]

        # Add message to session
        session["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        print(f"[AGENT] Message added to session (total: {len(session['messages'])})")

        # Analyze message
        analysis = self.analyze_message(message, user_id)

        # Create response (no Lambda forwarding - logs captured automatically)
        response = {
            "status": "success",
            "session_id": session_id,
            "user_id": user_id,
            "analysis": analysis,
            "message_count": len(session["messages"]),
            "user_memory": self.get_memory(user_id),
            "log_capture": "automatic_via_cloud_logging"
        }

        # Add response to session
        session["messages"].append({
            "role": "assistant",
            "content": str(analysis),
            "timestamp": datetime.utcnow().isoformat()
        })

        # Stream events (simulated streaming)
        events = [
            {"type": "session_start", "session_id": session_id},
            {"type": "analysis", "data": analysis},
            {"type": "response", "data": response}
        ]

        print(f"[AGENT] Stream complete: {len(events)} events")
        print(f"[{datetime.utcnow().isoformat()}] === Stream Query End ===")

        return events

    def query(self, **kwargs) -> Dict[str, Any]:
        """
        Entry point for direct queries (non-streaming)
        """
        message = kwargs.get('message', '')
        user_id = kwargs.get('user_id', 'default-user')
        session_id = kwargs.get('session_id')

        print(f"[AGENT] Query called: message='{message[:50]}...', user={user_id}, session={session_id}")

        # Process with streaming
        events = self.stream_query(message, user_id, session_id)

        # Return final response
        return events[-1]["data"]


# Create and deploy
print("[1/2] Creating Simple ADK Agent...")
print()

agent = SimpleADKAgent()

print("[2/2] Deploying to Vertex AI Reasoning Engine...")
engine = reasoning_engines.ReasoningEngine.create(
    agent,
    requirements=[
        "google-cloud-aiplatform>=1.38.0",
    ],
    display_name="adk-style-monitoring-agent",
    description="Simple ADK-style agent with sessions and memory (Cloud Logging capture only)",
    extra_packages=[],
)

print()
print("=" * 60)
print("Deployment Complete")
print("=" * 60)
print()
print(f"Engine ID: {engine.resource_name}")
print(f"Display Name: adk-style-monitoring-agent")
print()
print("Features:")
print("  - Session management (multi-turn conversations)")
print("  - User memory (error count tracking)")
print("  - Stream-style queries")
print("  - Automatic log capture to Cloud Logging")
print()
print("Logs flow automatically:")
print("  Reasoning Engine -> Cloud Logging -> Log Sink -> Pub/Sub -> AWS Lambda")
print()
print("Test with:")
print('  result = engine.query(')
print('      message="Database ERROR detected",')
print('      user_id="user-001",')
print('      session_id="session-abc"')
print('  )')
print()
print("No direct Lambda forwarding - pure Cloud Logging capture like basic-gcp-agent-working")
print()
