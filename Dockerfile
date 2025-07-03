# Stage 1: Set the base image
# We use a slim Python image to keep the final size smaller.
FROM python:3.9-slim

# Stage 2: Set environment variables
# Prevents Python from writing .pyc files and buffers output.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Stage 3: Set the working directory inside the container
WORKDIR /app

# Stage 4: Install dependencies
# We copy only the requirements file first to leverage Docker's caching.
# This layer will only be rebuilt if requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 5: Copy the application code into the container
# This includes our FastAPI app, the model pointer, etc.
COPY . .

# Stage 6: Expose the port the app will run on
# Our uvicorn server will run on port 8000.
EXPOSE 8000

# Stage 7: Define the command to run the application
# This is the command that will be executed when the container starts.
# We use 0.0.0.0 to make it accessible from outside the container.
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]