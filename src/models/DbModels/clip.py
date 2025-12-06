from sqlalchemy import Column, BigInteger, Float, Text, TIMESTAMP, ForeignKey, func
from src.core.database import Base


class Clip(Base):
    """Clip model"""
    __tablename__ = "clips"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=True)
    video_id = Column(BigInteger, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True)
    clip_url = Column(Text, unique=True, nullable=False)
    start_time_sec = Column(Float, nullable=True)
    end_time_sec = Column(Float, nullable=True)
    duration_sec = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<Clip(id={self.id}, video_id={self.video_id})>"
