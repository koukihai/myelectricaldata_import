FROM python:3.11-slim

ENV LANG fr_FR.UTF-8
ENV LC_ALL fr_FR.UTF-8
ENV TZ=Europe/Paris

RUN apt-get update && \
    apt-get install -y \
    locales  \
    git  \
    g++  \
    gcc  \
    libpq-dev \
    && sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./app/pyproject.toml /app/pyproject.toml

RUN pip install --upgrade pip pip-tools setuptools \
    && pip-compile -o /app/requirements.txt /app/pyproject.toml \
    && pip install -r /app/requirements.txt \
    && mkdir /data /log

# Copying app last, to avoid busting docker cache
COPY ./app /app

CMD ["python", "-u", "/app/app.py"]
