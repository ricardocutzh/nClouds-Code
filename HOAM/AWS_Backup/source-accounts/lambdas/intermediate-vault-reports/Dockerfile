FROM python:3.13

RUN pip install boto3

WORKDIR /home

COPY . .

ENTRYPOINT ["python"]

CMD ["main.py"]