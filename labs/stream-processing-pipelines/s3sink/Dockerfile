FROM confluentinc/cp-kafka-connect

RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN pip3 install awscli

RUN wget -O /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64 && chmod +x /usr/local/bin/jq
COPY set_env.sh /etc/set_env.sh

CMD ["/etc/set_env.sh"]