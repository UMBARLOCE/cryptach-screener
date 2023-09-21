FROM python:3.10-buster

RUN apt-get -y update

WORKDIR /usr/src/app/screener

COPY requirements.txt /usr/src/app/screener
RUN pip install -r /usr/src/app/screener/requirements.txt
COPY . /usr/src/app/screener

CMD ["python3", "-m", "main"]