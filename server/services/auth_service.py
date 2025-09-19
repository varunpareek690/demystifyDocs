from typing import Optional
from datetime import datetime, timedelta
from core.firebase_config import get_firestore_client
from core.security import verify_password, get_password_hash, create_access_token
from models.auth import UserRegister, UserLogin, User
from utils.exceptions import AuthenticationError, ValidationError
import uuid

class AuthService:
    def __init__(self):
        self.db = get_firestore_client()
        self.users_collection = self.db.collection('users')

    async def register_user(self, user_data: UserRegister) -> dict:
        """Register a new user."""
        # Check if user already exists
        existing_user = self.users_collection.where('email', '==', user_data.email).limit(1).get()
        if len(list(existing_user)) > 0:
            raise ValidationError("Email already registered")

        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password)
        
        user_doc = {
            'uid': user_id,
            'email': user_data.email,
            'full_name': user_data.full_name,
            'password_hash': hashed_password,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }

        # Save to Firestore
        self.users_collection.document(user_id).set(user_doc)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user_data.email, "uid": user_id},
            expires_delta=timedelta(minutes=30)
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})
        }

    async def authenticate_user(self, login_data: UserLogin) -> dict:
        """Authenticate user login."""
        # Find user by email
        users = self.users_collection.where('email', '==', login_data.email).limit(1).get()
        users_list = list(users)
        
        if not users_list:
            raise AuthenticationError("Invalid credentials")

        user_doc = users_list[0].to_dict()
        
        # Verify password
        if not verify_password(login_data.password, user_doc['password_hash']):
            raise AuthenticationError("Invalid credentials")

        # Check if user is active
        if not user_doc.get('is_active', True):
            raise AuthenticationError("Account is inactive")

        # Create access token
        access_token = create_access_token(
            data={"sub": user_doc['email'], "uid": user_doc['uid']},
            expires_delta=timedelta(minutes=30)
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})
        }

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        users = self.users_collection.where('email', '==', email).limit(1).get()
        users_list = list(users)
        
        if not users_list:
            return None

        user_doc = users_list[0].to_dict()
        return User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})