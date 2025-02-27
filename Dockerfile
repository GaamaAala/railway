FROM python:3.9  # Use at least Python 3.7 or higher
WORKDIR /app
COPY . .
RUN python -m venv venv
RUN . venv/bin/activate && pip install -r requirements.txt
CMD ["python", "main.py"]
