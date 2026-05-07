FROM python:3.11-slim
WORKDIR /app
# Added watchdog to the requirements
RUN pip install flask requests boto3 watchdog
COPY main.py .
EXPOSE 3001
CMD ["python", "main.py"]