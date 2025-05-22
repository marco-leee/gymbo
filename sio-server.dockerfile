FROM bitnami/python:3.12

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update 

RUN apt-get install -y libgl1 || true && \
    apt-get install -y libgl1

RUN apt-get install -y libglib2.0-0 libsm6 libxrender1 libxext6

WORKDIR /app

COPY backend/src /app
COPY backend/poetry.lock /app/poetry.lock
COPY backend/pyproject.toml /app/pyproject.toml

RUN pip install poetry && \
    poetry install

EXPOSE 10000

CMD ["poetry", "run", "python", "sio-server.py"]