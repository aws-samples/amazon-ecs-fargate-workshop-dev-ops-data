FROM ubuntu:latest

RUN apt-get update
RUN apt-get -y install python3-pip
RUN pip3 install paramiko
RUN pip3 install boto3

COPY app.py /opt/app.py

CMD ["/usr/bin/python3", "/opt/app.py"]
