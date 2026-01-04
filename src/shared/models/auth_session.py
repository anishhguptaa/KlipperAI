from sqlalchemy import Column, BigInteger, String, Text, TIMESTAMP, Boolean, ForeignKey, UUID
from sqlalchemy.orm import relationship
from src.shared.core.database import Base
from sqlalchemy import func, UniqueConstraint


class AuthSession(Base):
    """Auth session model for tracking user sessions and refresh tokens"""
    __tablename__ = "auth_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Who this session belongs to
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Device / browser identifier (cookie-based UUID)
    device_id = Column(UUID, nullable=False)
    
    # Hash of the CURRENT refresh token (never store plaintext)
    refresh_token_hash = Column(Text, nullable=False, unique=True)
    
    # Session state
    revoked = Column(Boolean, nullable=False, default=False)
    
    # Absolute session expiry (hard cap)
    expires_at = Column(TIMESTAMP, nullable=False)
    
    # Metadata (security + observability)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    last_used_at = Column(TIMESTAMP, nullable=True)
    revoked_at = Column(TIMESTAMP, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="auth_sessions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'device_id', name='uq_user_device'),
    )

    def __repr__(self):
        return f"<AuthSession(id={self.id}, user_id={self.user_id}, device_id={self.device_id}, revoked={self.revoked})>"
