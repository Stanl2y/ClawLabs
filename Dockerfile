FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN python -m pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md .python-version ./
COPY src ./src
COPY tests ./tests
COPY fixtures ./fixtures
COPY scenarios ./scenarios

RUN uv sync --frozen --dev

CMD ["uv", "run", "pytest"]
