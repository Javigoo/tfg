FROM python:3.7

COPY requirements.txt /
WORKDIR /
RUN pip install -r requirements.txt
COPY *.py /
CMD ["python", "bandwidth.py"]
CMD ["gunicorn", "api:api", "-b", "0.0.0.0:8000"]
