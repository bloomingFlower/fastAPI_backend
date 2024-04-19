from sqlalchemy.orm import Session
from sqlalchemy import or_
import models
import schemas


# 파일 정보 조회
def get_file(db: Session, file_id: int):
    return db.query(models.File).filter(models.File.id == file_id).first()


# 파일 목록 조회
def get_files(db: Session, skip: int = 0, limit: int = 100, filename: str = None):
    if filename:  # 파일명 검색
        files = db.query(models.File).filter(or_(models.File.filename.like(f"%{filename}%"))).order_by(
            models.File.id).offset(skip).limit(limit).all()
    else:  # 전체 파일 목록 조회
        files = db.query(models.File).order_by(models.File.id).offset(skip).limit(limit).all()
    return files


# 전체 파일 수 조회
def get_total_files(db: Session):
    return db.query(models.File).count()


# 파일명으로 파일 조회
def get_file_by_name(db: Session, filename: str):
    return db.query(models.File).filter_by(filename=filename).first()


# 파일 생성
def create_file(db: Session, file: schemas.FileCreate):
    db_file = models.File(**file.dict())
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


# 파일 삭제
def delete_file(db: Session, file_id: int):
    db_file = db.query(models.File).filter(models.File.id == file_id).first()
    db.delete(db_file)
    db.commit()
    return db_file


# 분석 결과 조회
def get_analysis(db: Session, analysis_id: int):
    return db.query(models.Analysis).order_by(models.Analysis.id.desc()).first()


# 분석 결과 목록 조회
def get_analysislist(db: Session, skip: int, limit: int):
    return db.query(models.Analysis).offset(skip).limit(limit).all()


# 분석 결과 생성
def create_analysis(db: Session, analysis: schemas.AnalysisCreate):
    if 'errorMessage' in analysis.dict():
        return {"error": analysis['errorMessage']}
    else:
        db_analysis = models.Analysis(**analysis.dict(exclude={"grid_results"}))
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

        # Save grid results
        for grid_result_data in analysis.grid_results:
            grid_result = models.GridResult(**grid_result_data.dict(), analysis_id=db_analysis.id)
            db.add(grid_result)
        db.commit()

        return db_analysis


# 분석 결과 삭제
def delete_analysis(db: Session, analysis_id: int):
    db_analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    db.delete(db_analysis)
    db.commit()
    return db_analysis


# 그리드 결과 조회
def get_grid_results_by_analysis_id(db: Session, analysis_id: int):
    return db.query(models.GridResult).filter(models.GridResult.analysis_id == analysis_id).all()


# 그리드 결과 삭제
def delete_grid_results_by_analysis_id(db: Session, analysis_id: int):
    db.query(models.GridResult).filter(models.GridResult.analysis_id == analysis_id).delete()
    db.commit()
