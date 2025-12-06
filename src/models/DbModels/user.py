from sqlalchemy import Column, BigInteger, String, Text, TIMESTAMP, func
from src.core.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=True)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
