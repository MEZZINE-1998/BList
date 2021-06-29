FROM python:3.7

WORKDIR /app
ADD . /app

# Install dependencies
RUN pip install -r requirements.txt

# Run the application:
CMD ["python", "app.py"]
