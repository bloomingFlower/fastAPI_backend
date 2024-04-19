################################################
# Developer: Jaeyoung Yun (yourrubber@duck.com)
# Development Date: 2024.04.05
# Version: v1
# Description: FastAPI 서버 구동
# - 파일 업로드
# - 파일 다운로드
# - 파일 목록 조회
# - 파일 삭제
# - 파일 분석
# - 분석 결과 조회
# - 분석 히스토리 삭제
# - 그리드 결과 조회
################################################

from PIL import Image
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import crud, schemas, analysis
from database import Base, engine, SessionLocal
from starlette.responses import FileResponse
import hashlib
from typing import List
import re
import os
from openslide import OpenSlide
from slide_extensions import SLIDE_EXTENSIONS
import magic

# DB 테이블 생성
Base.metadata.create_all(engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# For Testing
origins = [
    "*"
]

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 이미지 크기 제한 해제
Image.MAX_IMAGE_PIXELS = None
# 파일 저장 경로
upload_path = 'uploads'


# DB 세션 생성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 루트 테스트
@app.get("/")
async def root():
    return {"Status": "OK"}


# 파일 업로드
@app.post("/upload_files", response_model=List[schemas.File])
async def upload_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    response = []
    for file in files:
        # 파일명 체크
        pattern = r'^[^<>:"/\\|?*]+$'
        if not re.match(pattern, file.filename):
            raise HTTPException(status_code=400, detail="Invalid filename")

        # 파일 중복 체크
        db_file = crud.get_file_by_name(db, file.filename)
        if db_file:
            raise HTTPException(status_code=400, detail="File already uploaded")

        # 파일 저장 디렉토리 생성
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        # 파일 저장
        file_location = f'{upload_path}/{file.filename}'
        with open(file_location, 'wb') as f:
            f.write(file.file.read())
        file.file.seek(0)  # Reset file pointer to start

        # 파일 타입 체크
        mime_type = magic.from_file(file_location, mime=True)
        if mime_type not in SLIDE_EXTENSIONS and not mime_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type")

        # Slide 이미지 타입 분기 처리
        if file.content_type in SLIDE_EXTENSIONS:
            slide = OpenSlide(f'{upload_path}/{file.filename}')
            width, height = slide.dimensions
        else:
            # 그 외 일반 이미지 타입
            image = Image.open(file.file)
            width, height = image.size

        # 파일 정보 저장
        filetype = mime_type  # 파일 타입
        size = file.file.tell()  # 파일 크기
        file.file.seek(0)  # 파일 포인터 초기화
        checksum = hashlib.md5(file.file.read()).hexdigest()  # 파일 체크섬
        file.file.seek(0)  # 파일 포인터 초기화

        file_info = crud.create_file(db=db, file=schemas.FileCreate(filename=file.filename, width=width, height=height,
                                                                    filetype=filetype, size=size, checksum=checksum))
        response.append(file_info)
    return response


# 파일 다운로드
@app.get("/download/{file_id}")
async def download_file(file_id: int, db: Session = Depends(get_db)):
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = f'{upload_path}/{db_file.filename}'
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found in the directory")

    return FileResponse(file_path, filename=db_file.filename)


# 파일 목록 조회
@app.get("/files", response_model=List[schemas.File])
async def list_files(skip: int = 0, limit: int = 3, filename: str = None, db: Session = Depends(get_db)):
    files = crud.get_files(db, skip=skip, limit=limit, filename=filename)
    return files


# 파일 삭제
@app.delete("/files/{file_id}")
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # 파일 관련 analysis, grid results 삭제
    for analysis in db_file.analysis:
        crud.delete_grid_results_by_analysis_id(db=db, analysis_id=analysis.id)
        crud.delete_analysis(db=db, analysis_id=analysis.id)

    try:
        os.remove(f'{upload_path}/{db_file.filename}')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found in the directory")

    crud.delete_file(db=db, file_id=file_id)
    return {"message": "File and related analysis and grid results deleted successfully"}


# 파일 분석
@app.post("/analyze/{file_id}", response_model=schemas.Analysis)
async def analyze_file(file_id: int, db: Session = Depends(get_db)):
    # 파일 조회
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        # 분석 시행
        analysis_data = analysis.analyze_file_content(db, file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 분석 결과 저장
    return crud.create_analysis(db=db, analysis=analysis_data)


# 분석 결과 조회
@app.get("/history", response_model=List[schemas.Analysis])
async def list_analysis_history(skip: int = 0, limit: int = 3, db: Session = Depends(get_db)):
    analysis = crud.get_analysislist(db, skip=skip, limit=limit)
    return analysis


# 분석 히스토리 삭제
@app.delete("/history/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    db_analysis = crud.get_analysis(db, analysis_id=analysis_id)
    if db_analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # 분석 그리드 삭제
    crud.delete_grid_results_by_analysis_id(db=db, analysis_id=analysis_id)
    # 분석 결과 삭제
    crud.delete_analysis(db=db, analysis_id=analysis_id)

    return {"message": "Analysis deleted successfully"}


# 그리드 결과 조회
@app.get("/grid_results/{analysis_id}", response_model=List[schemas.GridResultBase])
async def get_grid_results_by_analysis_id(analysis_id: int, db: Session = Depends(get_db)):
    grid_results = crud.get_grid_results_by_analysis_id(db, analysis_id=analysis_id)
    if grid_results is None:
        raise HTTPException(status_code=404, detail="Grid results not found")
    return grid_results


# 파일 읽기
def get_file_content(filename: str):
    with open(f'{upload_path}/{filename}', 'rb') as f:
        content = f.read()
    return content
