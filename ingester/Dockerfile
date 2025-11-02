FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

COPY requirements.txt .

# Install dependencies system-wide (not in venv)
RUN uv pip install --system -r requirements.txt

COPY . .

CMD ["python", "app.py"]
