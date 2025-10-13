# Dockerfile.gradio
FROM python:3.12

WORKDIR /app

COPY ./gradio/requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN apt-get update
RUN apt-get install -y vim iputils-ping telnet net-tools

# Specify the Gradio script file
ENTRYPOINT python gradio/gradio_interface.py