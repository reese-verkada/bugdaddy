FROM python:3.7.7-buster

RUN apt update
RUN apt install -y xmlsec1 awscli jq

WORKDIR /usr/src/app/backend

COPY backend/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/*.py ./
COPY backend/db/ ./db/

WORKDIR /usr/src/app/

COPY run.py ./
COPY run.sh ./
RUN chmod +x run.sh

CMD ["./run.sh"]