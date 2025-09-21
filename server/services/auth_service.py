from typing import Optional
from datetime import datetime, timedelta
from core.firebase_config import get_firestore_client
from core.security import create_access_token
from models.auth import GoogleOAuthLogin, User
from utils.exceptions import AuthenticationError
from services.google_oauth_service import GoogleOAuthService
import uuid

class AuthService:
    def __init__(self):
        self.db = get_firestore_client()
        self.users_collection = self.db.collection('users')
        self.google_oauth_service = GoogleOAuthService()

    async def authenticate_google_user(self, oauth_data: GoogleOAuthLogin) -> dict:
        """Authenticate user via Google OAuth - create account if doesn't exist."""
        # Verify Google token
        google_user_info = await self.google_oauth_service.verify_google_token(oauth_data.id_token)
        
        if not google_user_info:
            raise AuthenticationError("Invalid Google token")
        
        if not google_user_info['email_verified']:
            raise AuthenticationError("Email not verified with Google")

        # Check if user exists by email
        existing_users = self.users_collection.where('email', '==', google_user_info['email']).limit(1).get()
        existing_users_list = list(existing_users)

        if existing_users_list:
            # User exists - update info if needed
            user_doc = existing_users_list[0].to_dict()
            user_id = user_doc['uid']
            
            # Update user info (in case name or picture changed)
            updates = {
                'full_name': google_user_info['full_name'],
                'picture': google_user_info['picture'],
                'google_id': google_user_info['google_id']  # Ensure Google ID is set
            }
            self.users_collection.document(user_id).update(updates)
            user_doc.update(updates)
        else:
            # Create new user from Google info
            user_id = str(uuid.uuid4())
            user_doc = {
                'uid': user_id,
                'email': google_user_info['email'],
                'full_name': google_user_info['full_name'],
                'google_id': google_user_info['google_id'],
                'picture': google_user_info['picture'],
                'created_at': datetime.utcnow().isoformat(),
                'is_active': True,
                'auth_provider': 'google'
            }
            self.users_collection.document(user_id).set(user_doc)

        # Create access token
        access_token = create_access_token(
            data={"sub": user_doc['email'], "uid": user_doc['uid']},
            expires_delta=timedelta(hours=24)
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": User(**user_doc)
        }

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        users = self.users_collection.where('email', '==', email).limit(1).get()
        users_list = list(users)
        
        if not users_list:
            return None

        user_doc = users_list[0].to_dict()
        return User(**user_doc)

    async def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID."""
        users = self.users_collection.where('google_id', '==', google_id).limit(1).get()
        users_list = list(users)
        
        if not users_list:
            return None

        user_doc = users_list[0].to_dict()
        return User(**user_doc)