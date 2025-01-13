# Dockerfile.gradio
FROM python:3.12

WORKDIR /app

COPY ./gradio/requirements.txt .

RUN pip install -r requirements.txt

COPY . .

# Specify the Gradio script file
ENTRYPOINT python gradio/gradio_interface.py