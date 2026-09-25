FROM python:3.14-slim

WORKDIR /link

ADD . /link

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

CMD ["python", "main.py"]
