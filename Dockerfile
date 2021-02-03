FROM python:3.8
LABEL MAINTAINER="kpachhai"

ADD requirements.txt /src/
RUN cd /src && pip install -r requirements.txt

ADD app /src/app
ADD .env.example /src/.env

WORKDIR /src

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:application"]


