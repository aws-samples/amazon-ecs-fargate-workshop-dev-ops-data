FROM ubuntu:latest

RUN apt-get update
RUN apt-get -y install python3-pip
RUN pip3 install kafka-python
RUN pip3 install pymongo
RUN pip3 install boto3

COPY app.py /opt/app.py
COPY rds-combined-ca-bundle.pem /opt/rds-combined-ca-bundle.pem

CMD ["/usr/bin/python3", "/opt/app.py"]