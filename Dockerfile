# Use a newer Python 3.10 base image
FROM python:3.10-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt to the working directory
COPY requirements.txt .

# Install all Python dependencies. Also install 'tree' for better debugging.
RUN apt-get update && apt-get install -y tree && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire 'src' folder from host to /app/src in the container
COPY src/ /app/src/

# Create /tmp directory if it doesn't exist
RUN mkdir -p /tmp

# Create 'config' directory in the container
RUN mkdir -p /app/config

# Exposed port: Streamlit app runs on port 8501 by default.
EXPOSE 8501

# Command to run the application when the container starts.
CMD ["streamlit", "run", "src/ui/streamlit_app.py"]
