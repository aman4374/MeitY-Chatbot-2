# 1. Base Image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the application code (the backend and the streamlit app)
COPY ./backend ./backend
COPY app.py .

# 5. Expose the port Streamlit runs on
EXPOSE 8501

# 6. Define the command to run the app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]