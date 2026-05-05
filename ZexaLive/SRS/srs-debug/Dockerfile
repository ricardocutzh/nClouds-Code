FROM python:3.11-slim
WORKDIR /app
RUN pip install flask requests
COPY main.py .
EXPOSE 3001
CMD ["python", "main.py"]