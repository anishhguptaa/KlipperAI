import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import bcrypt
import jwt
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.core.config import settings
from src.models.DbModels import User, AuthSession


class AuthService:
    """Service class for handling authentication operations"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def generate_tokens(user_id: int) -> Tuple[str, str]:
        """Generate access and refresh tokens for a user"""
        # Access token payload
        access_payload = {
            "user_id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        # Refresh token payload
        refresh_payload = {
            "user_id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        return access_token, refresh_token

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            if payload.get("type") != token_type:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def hash_refresh_token(refresh_token: str) -> str:
        """Hash a refresh token for secure storage"""
        return hashlib.sha256(refresh_token.encode()).hexdigest()

    @staticmethod
    def create_user(db: Session, name: str, email: str, password: str) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password and create user
        password_hash = AuthService.hash_password(password)
        user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        return user

    @staticmethod
    def create_auth_session(
        db: Session, 
        user_id: int, 
        refresh_token: str, 
        device_id: Optional[str] = None
    ) -> AuthSession:
        """Create a new auth session"""
        if not device_id:
            device_id = str(uuid.uuid4())
        
        # Revoke any existing session for this user-device combination
        existing_session = db.query(AuthSession).filter(
            and_(
                AuthSession.user_id == user_id,
                AuthSession.device_id == device_id,
                AuthSession.revoked == False
            )
        ).first()
        
        if existing_session:
            existing_session.revoked = True
            existing_session.revoked_at = datetime.now(timezone.utc)
        
        # Create new session
        refresh_token_hash = AuthService.hash_refresh_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        auth_session = AuthSession(
            user_id=user_id,
            device_id=device_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at
        )
        
        db.add(auth_session)
        db.commit()
        db.refresh(auth_session)
        return auth_session

    @staticmethod
    def validate_refresh_token(db: Session, refresh_token: str) -> Optional[AuthSession]:
        """Validate a refresh token and return the associated session"""
        # Decode the refresh token to get the payload
        payload = AuthService.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        # Hash the token to compare with stored hash
        refresh_token_hash = AuthService.hash_refresh_token(refresh_token)
        
        # Find the session
        session = db.query(AuthSession).filter(
            and_(
                AuthSession.user_id == user_id,
                AuthSession.refresh_token_hash == refresh_token_hash,
                AuthSession.revoked == False,
                AuthSession.expires_at > datetime.now(timezone.utc)
            )
        ).first()
        
        if session:
            # Update last used timestamp
            session.last_used_at = datetime.now(timezone.utc)
            db.commit()
        
        return session

    @staticmethod
    def revoke_session(db: Session, session: AuthSession) -> None:
        """Revoke an auth session"""
        session.revoked = True
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()

    @staticmethod
    def revoke_all_user_sessions(db: Session, user_id: int) -> None:
        """Revoke all sessions for a user (security breach response)"""
        sessions = db.query(AuthSession).filter(
            and_(
                AuthSession.user_id == user_id,
                AuthSession.revoked == False
            )
        ).all()
        
        for session in sessions:
            session.revoked = True
            session.revoked_at = datetime.now(timezone.utc)
        
        db.commit()

    @staticmethod
    def rotate_refresh_token(
        db: Session, 
        old_session: AuthSession, 
        user_id: int
    ) -> Tuple[str, str, AuthSession]:
        """Rotate refresh token - revoke old and create new"""
        # Revoke the old session
        AuthService.revoke_session(db, old_session)
        
        # Generate new tokens
        access_token, refresh_token = AuthService.generate_tokens(user_id)
        
        # Create new session
        new_session = AuthService.create_auth_session(
            db, user_id, refresh_token, str(old_session.device_id)
        )
        
        return access_token, refresh_token, new_session
