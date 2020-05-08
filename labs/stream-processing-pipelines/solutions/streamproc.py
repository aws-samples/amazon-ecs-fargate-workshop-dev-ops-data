# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from kafka import KafkaConsumer
import pymongo
import hashlib
import boto3
import os

# environment variables for service discovery
TOPIC_NAME = os.environ['TOPIC_NAME']
NAMESPACE = os.environ['NAMESPACE']
MSK_SERVICE = os.environ['MSK_SERVICE']
DDB_SERVICE = os.environ['DDB_SERVICE']

print("Looking up broker ARN")
svc_client = boto3.client('servicediscovery')
response = svc_client.discover_instances(
    NamespaceName=NAMESPACE,
    ServiceName=MSK_SERVICE
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

print("Looking up DocumentDB endpoint")
response = svc_client.discover_instances(
    NamespaceName=NAMESPACE,
    ServiceName=DDB_SERVICE
)
ddb_endpoint = ''
for svc_instance in response['Instances']:
    svc_instance_id = svc_instance['InstanceId']
    if 'ReadEndpoint' not in svc_instance_id:
        ddb_endpoint = svc_instance['Attributes']['endpoint'] 
        docdbuser = svc_instance['Attributes']['user'] 
        docdbpass = svc_instance['Attributes']['password'] 

# To consume latest messages and auto-commit offsets
print("")
consumer = KafkaConsumer(TOPIC_NAME,
            bootstrap_servers=broker_string,
            security_protocol = 'SSL')

client = pymongo.MongoClient("mongodb://{0}:{1}@{2}:27017/?ssl=true&ssl_ca_certs=/opt/rds-combined-ca-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred".format(
    docdbuser,
    docdbpass,
    ddb_endpoint
))
db = client.kafka
col = db.hashed

# This loop will run forever as long as we're getting messages
for message in consumer:
    raw_value = message.value.decode('utf-8')
    print("Found record {0}".format(raw_value))
    hashvalue = hashlib.sha224(raw_value.encode('utf-8')).hexdigest()
    col.insert_one({'value':hashvalue})
