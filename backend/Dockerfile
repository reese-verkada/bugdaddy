FROM python:3.7.7-buster

RUN apt update
RUN apt install -y xmlsec1 awscli jq

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY *.py /usr/src/app/
COPY run.sh /usr/src/app/
COPY db/ /usr/src/app/db/

RUN chmod +x run.sh

CMD ["./run.sh"]