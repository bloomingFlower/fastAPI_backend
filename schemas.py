from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from FileStatus import FileStatus


# 파일 기본 정보
class FileBase(BaseModel):
    filename: str
    status: Optional[str] = FileStatus.UPLOADED.value
    width: Optional[int] = None
    height: Optional[int] = None
    filetype: Optional[str] = None
    size: Optional[int] = None
    checksum: Optional[str] = None


# 파일 생성
class FileCreate(FileBase):
    pass


# 파일 정보
class File(FileBase):
    id: int
    upload_time: datetime
    analysis: List['Analysis'] = []

    class Config:
        from_attributes = True


# 그리드 결과
class GridResultBase(BaseModel):
    file_id: int
    intratumoral_til_density_min: float
    intratumoral_til_density_avg: float
    intratumoral_til_density_max: float
    stromal_til_density_min: float
    stromal_til_density_avg: float
    stromal_til_density_max: float


# 분석 결과 기본 정보
class AnalysisBase(BaseModel):
    file_id: int
    decision: bool
    score: float


# 분석 결과 생성
class AnalysisCreate(AnalysisBase):
    file_id: int
    grid_results: List[GridResultBase]


# 분석 결과 정보
class Analysis(AnalysisBase):
    id: int

    class Config:
        from_attributes = True


