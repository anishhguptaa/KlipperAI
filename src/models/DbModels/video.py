from sqlalchemy import Column, BigInteger, Integer, Text, TIMESTAMP, ForeignKey, func
from src.core.database import Base


class Video(Base):
    """Video model"""
    __tablename__ = "videos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    blob_url = Column(Text, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<Video(id={self.id}, user_id={self.user_id})>"
