FROM python:3.7
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV FLASK_APP app.py
ENTRYPOINT ["python", "-m", "flask", "run", "--host=0.0.0.0"]