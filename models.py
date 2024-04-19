from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


# 파일 정보 테이블
class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True)
    status = Column(String, default="uploaded")
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    width = Column(Integer)
    height = Column(Integer)
    filetype = Column(String)
    size = Column(String)
    checksum = Column(String)
    # 관계 설정
    grid_results = relationship("GridResult", back_populates="file")
    analysis = relationship("Analysis", back_populates="file")


# 분석 결과 테이블
class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    decision = Column(Boolean)
    score = Column(Float)
    # 관계 설정
    file = relationship("File", back_populates="analysis")


# 그리드 결과 테이블
class GridResult(Base):
    __tablename__ = "grid_results"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    analysis_id = Column(Integer, ForeignKey("analysis.id"))
    intratumoral_til_density_min = Column(Float)
    intratumoral_til_density_avg = Column(Float)
    intratumoral_til_density_max = Column(Float)
    stromal_til_density_min = Column(Float)
    stromal_til_density_avg = Column(Float)
    stromal_til_density_max = Column(Float)
    # 관계 설정
    file = relationship("File", back_populates="grid_results")