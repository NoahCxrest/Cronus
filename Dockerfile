# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY main.py /app/
COPY config.json /app/
COPY menus.py /app/

# Copy all files from the Cogs directory into the container at /app/Cogs
COPY Cogs /app/Cogs/

# Generate requirements.txt (if needed)
RUN pip freeze > requirements.txt

# Install dependencies
RUN pip3 install discord python-dotenv psutil motor jishaku -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run bot.py when the container launches
CMD ["python", "main.py"]
