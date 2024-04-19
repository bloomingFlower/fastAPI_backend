import random

from FileStatus import FileStatus
import crud
import schemas
from models import GridResult
from sqlalchemy.orm import Session


def analyze_file_content(db: Session, file_id: int):
    # Dummy analysis logic
    decision = random.choice([True, False])  # 랜덤 결정
    score = random.random()  # 랜덤 스코어 0.0 and 1.0

    # 더미 결과 생성
    grid_results = []

    db_file = crud.get_file(db, file_id=file_id)
    db_file.status = FileStatus.ANALYZING.value
    db.commit()
    try:
        if random.choice([True, False]):  # 50% 확률로 분석 실패 발생
            raise Exception("Analyze file(fileId '"+ str(file_id) +"' content failed. Please try again later.")

        for _ in range(20):  # 20개의 그리드 결과 생성
            intratumoral_til_density = generate_random_min_avg_max()
            stromal_til_density = generate_random_min_avg_max()

            grid_result = GridResult(
                file_id=file_id,
                intratumoral_til_density_min=intratumoral_til_density["min"],
                intratumoral_til_density_avg=intratumoral_til_density["avg"],
                intratumoral_til_density_max=intratumoral_til_density["max"],
                stromal_til_density_min=stromal_til_density["min"],
                stromal_til_density_avg=stromal_til_density["avg"],
                stromal_til_density_max=stromal_til_density["max"],
            )
            grid_results.append(grid_result.__dict__)

        db_file.status = FileStatus.ANALYZED.value
        db.commit()
        return schemas.AnalysisCreate(file_id=file_id, decision=decision, score=score, grid_results=grid_results)
    except Exception as e:
        db_file.status = FileStatus.FAILED.value
        db.commit()

        raise e

# 랜덤 min, avg, max 값 생성
def generate_random_min_avg_max():
    values = sorted([random.random() for _ in range(3)])
    return {
        "min": values[0],
        "avg": values[1],
        "max": values[2],
    }
