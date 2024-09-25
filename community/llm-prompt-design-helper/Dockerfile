FROM ubuntu:22.04

RUN apt-get -y update
RUN apt-get -y install python3 python3-pip

# RUN mkdir /chat_ui
# COPY chat_ui.py /chat_ui
# COPY config.yaml /chat_ui
# COPY api_request.py /chat_ui
COPY requirements.txt /chat_ui/
WORKDIR /chat_ui/

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3"]
CMD ["-u", "chat_ui.py"]
