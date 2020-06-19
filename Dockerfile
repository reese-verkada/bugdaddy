FROM python:3.7.7-buster

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY *.py /usr/src/app/
COPY db/ /usr/src/app/db/

CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app"]