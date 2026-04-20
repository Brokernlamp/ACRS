from typing import Optional, Dict, Any
from database import SessionLocal
from database.crud import get_user_by_id
from auth import get_current_user
import gradio as gr

class SessionManager:
    """Manages user sessions in Gradio"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, session_id: str, user_id: int, token: str) -> None:
        """Create a new user session"""
        self.sessions[session_id] = {
            "user_id": user_id,
            "token": token,
            "current_client_id": None,
        }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs) -> None:
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(kwargs)
    
    def clear_session(self, session_id: str) -> None:
        """Clear session data"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_current_user(self, session_id: str):
        """Get current user from session"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        db = SessionLocal()
        try:
            user = get_current_user(db, session["token"])
            return user
        finally:
            db.close()
    
    def is_authenticated(self, session_id: str) -> bool:
        """Check if user is authenticated"""
        return self.get_current_user(session_id) is not None
    
    def get_current_client_id(self, session_id: str) -> Optional[int]:
        """Get current selected client ID"""
        session = self.get_session(session_id)
        return session.get("current_client_id") if session else None
    
    def set_current_client_id(self, session_id: str, client_id: int) -> None:
        """Set current selected client ID"""
        self.update_session(session_id, current_client_id=client_id)

# Global session manager
session_manager = SessionManager()


def require_auth(func):
    """Decorator to require authentication for a function"""
    def wrapper(*args, **kwargs):
        # In Gradio, we'll pass session_id as first argument
        session_id = args[0] if args else None
        if not session_id or not session_manager.is_authenticated(session_id):
            return gr.update(visible=True), "Please log in first."
        return func(*args, **kwargs)
    return wrapper


def get_session_id() -> str:
    """Generate a session ID (in real app, this would be from Gradio's session)"""
    import uuid
    return str(uuid.uuid4())