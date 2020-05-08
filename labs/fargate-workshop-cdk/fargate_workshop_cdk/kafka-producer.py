# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka import KafkaAdminClient
from kafka.admin import NewTopic
import time
import os
import boto3

# constants
MIN_TIME_REMAINING_MILLIS = 30 * 1000
SLEEP_SECONDS = 5

# environment variables
NAMESPACE = os.environ['NAMESPACE']
SERVICE = os.environ['SERVICE']
TOPIC_NAME = os.environ['TOPIC_NAME']

def main(event, context):

    print("Looking up broker ARN")
    svc_client = boto3.client('servicediscovery')
    response = svc_client.discover_instances(
        NamespaceName=NAMESPACE,
        ServiceName=SERVICE
    )
    broker_arn = response['Instances'][0]['Attributes']['broker_arn']
    print("Got broker ARN {0}".format(broker_arn))

    print("Looking up broker string")
    msk_client = boto3.client('kafka')
    response = msk_client.get_bootstrap_brokers(
        ClusterArn=broker_arn
    )
    broker_string = response['BootstrapBrokerStringTls']
    print("Got broker string {0}".format(broker_string))

    # make sure topic exists
    print("Checking if topic {0} exists".format(TOPIC_NAME))
    kclient = KafkaConsumer(bootstrap_servers=broker_string, security_protocol = 'SSL')
    existing_topics = kclient.topics()
    if TOPIC_NAME in existing_topics:
        print("Topic {0} exists".format(TOPIC_NAME))
    else:
        print("Topic {0} does not exist, creating".format(TOPIC_NAME))
        topic_list = []
        topic = NewTopic(name=TOPIC_NAME, num_partitions=1, replication_factor=1)
        topic_list.append(topic)
        kadmin = KafkaAdminClient(bootstrap_servers=broker_string, security_protocol = 'SSL')
        kadmin.create_topics(new_topics = topic_list)
        kadmin.close()
    kclient.close()

    producer = KafkaProducer(bootstrap_servers=broker_string, security_protocol = 'SSL')

    while True:
        remaining_time_millis = context.get_remaining_time_in_millis()

        if remaining_time_millis < MIN_TIME_REMAINING_MILLIS:
            print("Time left ({0}) is less than time required ({1}), exiting".format(str(remaining_time_millis), str(MIN_TIME_REMAINING_MILLIS)))
            break
        else:
            print("Time left ({0}) is greater than time required ({1}), sending".format(str(remaining_time_millis), str(MIN_TIME_REMAINING_MILLIS)))
            msg = "Kafka message sent at {0}".format(str(time.time()))
            producer.send(TOPIC_NAME, msg.encode('utf-8'))
            producer.flush()
            time.sleep(SLEEP_SECONDS)

    producer.close()
    print("All done")
