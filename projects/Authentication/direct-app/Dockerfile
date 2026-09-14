FROM python:3.12-slim

WORKDIR /srv/direct

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i http://pypi.home.ailexc.com/simple --trusted-host pypi.home.ailexc.com

COPY app.py jwks_auth.py ./

EXPOSE 8003

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"]
