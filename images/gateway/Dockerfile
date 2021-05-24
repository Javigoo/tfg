FROM python:3.7

COPY requirements.txt /
RUN pip install -r requirements.txt

RUN mkdir -p /kube
COPY /kube/config /kube/config

COPY gateway.py /
CMD ["python", "gateway.py"]
