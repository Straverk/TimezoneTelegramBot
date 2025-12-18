FROM python:alpine AS deps

COPY requirements.txt .

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade -r requirements.txt


FROM python:alpine

COPY ./bot /bot
WORKDIR /bot


COPY --from=deps /venv /venv
ENV PATH="/venv/bin:$PATH"


EXPOSE 80
CMD ["python3", "-X", "pycache_prefix=/tmp/pycache", "bot.py"]