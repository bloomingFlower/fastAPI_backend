FROM python:3.9

# OpenSlide 설치(python openslide 설치 전에 설치해야 함)
RUN apt-get update && apt-get install -y libopenslide-dev

WORKDIR /app

COPY ../requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY .. .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]