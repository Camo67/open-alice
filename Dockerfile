FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml requirements.txt README.md ./
COPY src/ ./src/
COPY tests/ ./tests/

RUN pip install --no-cache-dir -e ".[dev]"]

ENTRYPOINT ["alice"]
CMD ["--help"]
