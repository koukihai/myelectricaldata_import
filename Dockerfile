FROM python:3.11-slim

COPY ./app /app

RUN pip install --no-cache-dir --upgrade pip pip-tools setuptools \
    && pip-compile -o /app/requirements.txt /app/pyproject.toml \
    && pip install --no-cache-dir -r /app/requirements.txt

RUN mkdir /data /log

CMD ["python", "-u", "/app/main.py"]
