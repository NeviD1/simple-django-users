FROM python:3.11

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install poetry

COPY poetry.lock pyproject.toml docker-entrypoint.sh ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY src src

WORKDIR /app/src

EXPOSE 8000
