---
title: "Lab 2: Stream Processing"
date: 2020-04-10T10:35:36-06:00
weight: 15
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

In this lab, we'll see how to use Fargate tasks to work with data coming into our Kafka cluster.  We'll try two approaches:

* Processing the data directly in a Fargate task and storing some results in DocumentDB.
* Archiving Kafka data into an S3 bucket using Kafka Connect.

![Stream Processing Architecture](/images/dataeng-stream.png)

You can extend these patterns to include general queue processing paradigms, where the input is an SQS or Amazon MQ queue rather than a Kafka topic.  However, you should consider whether the input volume is high enough to warrant having tasks running all the time, versus just processing them with Lambda functions.

Let's start by creating a Fargate cluster for stream processing.  Although a DevOps team would create the cluster in a CI/CD pipeline and treat the cluster properties as code, we'll skip that step and just create a cluster using the CDK.  We don't intend to change anything on the cluster itself so we don't need to set up dependent CI/CD pipelines.

    cd fargate-workshop-cdk
    cdk deploy fargate-workshop-dataeng-cluster # This stack was likely created earlier as a dependency

### Process stream data and store in DocumentDB

Let's begin writing a Fargate service that reads data from Kafka and writes a simple aggregate into a DocumentDB table.  We will drive the lab through a CI/CD process, just as you would for a production system.  But we do need to register the task and service with Fargate before we start deploying via our pipeline.  To do that, we'll run a CDK script to bootstrap our service and build the pipeline skeleton.

#### Create a Git repository

Let's create a Git repository.  We'll do this manually as setting up development tools is often done by hand.

Follow the [guide](https://docs.aws.amazon.com/codecommit/latest/userguide/how-to-create-repository.html) to create a new repository in CodeCommit.  Name it `FargateStreamProcessor`.

Follow the instructions on the console to clone your new repo into a local folder in Cloud9.  For example:

    cd ~/environment
    git clone ssh://git-codecommit.<region>.amazonaws.com/v1/repos/FargateStreamProcessor

#### Push placeholder image

On the CLI:

    aws ssm get-parameter --name repo_uri

Note that `value` in the output, which is our ECR repository URI.  Use this in the following commands:

    docker pull nginx:latest
    docker tag nginx:latest <value>:latest
    $(aws ecr get-login --no-include-email)
    docker push <value>:latest


#### Check in source code

Go to your local copy of the `FargateStreamProcessor` repo:

    cd ~/environment/FargateStreamProcessor
    cp ../fargate-workshop/labs/stream-processing-pipelines/kafka_to_docdb/* .
    wget https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem
    git add .
    git commit -m "Initial commit"
    git push

This code just has a stub `Dockerfile` and `buildspec`.

#### Deploy the pipeline and prerequisites

Deploy our pipeline using the CDK.  Open a new terminal and enter:

    cd ~/environment/fargate-workshop/labs/fargate-workshop-cdk
    source ~/environment/fargate-workshop/.env/bin/activate
    cdk deploy fargate-workshop-dataeng-streams

This should trigger the pipeline to run.  It'll build the Docker image and publish it as a Fargate service.

Take a minute to review the code that generates our Fargate service:

    streamproc_task_definition = ecs.FargateTaskDefinition(
            scope = self, 
            id = "StreamProcTaskDef",
            cpu=1024,
            memory_limit_mib=2048
    )
    streamproc_task_definition.add_container(
            id = "StreamProcContainer",
            image=ecs.ContainerImage.fromEcrRepository(repository = repo, tag = 'latest'),
            logging=ecs.LogDrivers.awslogs(stream_prefix="StreamProcessing")
    )
    streamproc_service = ecs.FargateService(
            scope = self, 
            id = "StreamProcessingService",
            task_definition=streamproc_task_definition,
            assign_public_ip = False,
            security_group = docdbClientFirewall,
            cluster=cluster,
            desired_count = 1
    )
    streamproc_service.connections.add_security_group(kafkaClientFirewall)
    streamproc_scaling = streamproc_service.auto_scale_task_count(max_capacity=10)
    streamproc_scaling.scale_on_cpu_utilization("CpuScaling",
        target_utilization_percent=70
    )

The CDK hides most of the boilerplate associated with ECS services.  You can see some of the key details, like the amount of CPU and memory allocated for these tasks, which image we're using, the security groups, and the scaling policies.  Feel free to adjust these limits and redeploy the stack.

#### Adding application code

In your working directory of the CodeCommit repo for this lab, look at the `app.py` file.  It's just a stub that echoes a message every minute.  We need to put in our stream processing logic now.

Here are the requirements you should try to implement:

* Connect to our Kafka cluster as a consumer
* Connect to our DocumentDB cluster
* Poll the Kafka topic `MyTopic` for new messages
* As new messages come in, perform MD5 hashing to obfuscate the value, and write the hashed value into our database
* Avoid using hard-coded parameters.  Note that the container is passed in some environment variables that should help with service discovery.

A solution is found in `~/environment/fargate-workshop/labs/stream-processing-pipelines/solutions/streamproc.py`.  

Once you're satisfied with your code, check it into the Git repo and watch the pipeline deploy the new version.

#### Verify that our stream processor works

Let's check the data written into our database.  Before proceeding, follow these [instructions](https://docs.aws.amazon.com/documentdb/latest/developerguide/getting-started.connect.html) to connect to your DocumentDB instance.  The default password is `DocDbPass`.

Then from the `mongo-shell`:

    use kafka
    db.hashed.findOne()
    db.hashed.count()

You should see more and more records show up in this collection as our stream processor runs.

###  Archiving Kafka data into an S3 bucket using Kafka Connect.

Another common pattern in stream processing is to push incoming data into S3, making it available for downstream batch processing and machine learning.  This may happen instead of or in combination with inline stream processing.

In this part of the lab we'll use the [Kafka Connect S3 Sink](https://docs.confluent.io/current/connect/kafka-connect-s3/index.html).  We'll run the S3 Sink in a container and deploy it as an auto-scaling Fargate service.

We'll start with the [public Kafka Connect Docker image](https://hub.docker.com/r/confluentinc/cp-kafka-connect), but we need to make a couple modifications.  First, we need each worker (task) to advertise a unique host name, the task IP address.  With ECS we can't assign this in the task spec; we need to get the task IP at runtime when the task is launched, and provide it to the S3 Sink.  Second, we want to add a health checker to report accurate status.  The Kafka Connector normally reports healthy as long as the container is running, but we want to dig deeper into the status checks.  We'll use an open source [health checker](https://pypi.org/project/kafka-connect-healthcheck/) as a sidecar container in the task.

While we don't need to write any custom code, this section of the lab lets us see how to deploy multiple containers in a single task and use a very common Kafka add-on.

#### Create Kafka topics

The S3 Sink will use several Kafka topics for internal bookkeeping.  Create these now using a Kafka client.  On the Cloud 9 IDE, [download](https://kafka.apache.org/downloads) the Kafka distribution and unpack it.  Make sure you get a compatible version of Kafka; you can see the version of Kafka used in the MSK console.  In the Kafka directory, you'll run a command like this:

    echo 'security.protocol=SSL' > client.properties
    ./bin/kafka-topics.sh --create --bootstrap-server <Kafka bootstrap string> --replication-factor 3 --partitions 1 --topic <topic> --command-config client.properties

As a reminder, you can look up the Kafka bootstrap string by first identifying the broker ARN using service discovery, and then getting the list of bootstrap servers.

    sudo yum install -y jq
    sudo yum install -y java-1.8.0-openjdk-devel
    sudo alternatives --config java # select JDK 1.8
    sudo yum remove java-1.7.0-openjdk-devel
    aws servicediscovery list-namespaces # Find namespace FargateWorkshopNamespace and note the ID
    aws servicediscovery list-services --filters Name=NAMESPACE_ID,Values=<namespace id> # Find service whose name starts with CloudMapKafkaSvc
    BROKER_ARN=$(aws servicediscovery discover-instances --region $REGION --namespace-name FargateWorkshopNamespace --service-name $MSK_SERVICE | jq -r '.Instances[0].Attributes.broker_arn')
    BOOTSTRAP_SERVERS=$(aws kafka get-bootstrap-brokers --region $REGION --cluster-arn $BROKER_ARN | jq -r '.BootstrapBrokerStringTls')

Run that for these three topics:

* `kc_config` 
* `kc_status`
* `kc_offset`

#### Create Git repositories

Once again, let's create Git repositories for our source code, which in this case is just a custom Dockerfile and a shell script to launch the actual program with an environment variable set.

Follow the [guide](https://docs.aws.amazon.com/codecommit/latest/userguide/how-to-create-repository.html) to create two new repositories in CodeCommit.  Name them `FargateS3Sink` and `FargateS3SinkHealthCheck`.

Follow the instructions on the console to clone your new repos into local folders in Cloud9.

#### Push placeholder images

On the CLI, get the ECR URIs for the repos we'll use for the Kafka Connector and the health checker:

    aws ssm get-parameter --name repo_uri_s3_sink
    aws ssm get-parameter --name repo_uri_s3_sink_hc

Note that `value` in the output, which is our ECR repository URI.  Use this in the following commands:

    docker pull nginx:latest
    docker tag nginx:latest <value>:latest
    $(aws ecr get-login --no-include-email)
    docker push <value>:latest

Run the last three commands twice, one for each repo.

#### Check in source code

Go to your local copy of the `FargateS3Sink` repo:

    cd ~/environment/FargateS3Sink
    cp ~/environment/fargate-workshop/labs/stream-processing-pipelines/s3sink/* .
    git add .
    git commit -m "Initial commit"
    git push

Go to your local copy of the `FargateS3SinkHealthCheck` repo:

    cd ~/environment/FargateS3SinkHealthCheck
    cp ~/environment/fargate-workshop/labs/stream-processing-pipelines/s3sinkhc/* .
    git add .
    git commit -m "Initial commit"
    git push

#### Deploy the pipeline and prerequisites

Deploy our pipeline using the CDK:

    cd ~/environment/fargate-workshop/labs/fargate-workshop-cdk
    source ~/environment/fargate-workshop/.env/bin/activate
    cdk deploy fargate-workshop-dataeng-kafkaconnect

This should trigger the pipeline to run.  It'll build the Docker image and publish it as a Fargate service.

#### Configure Kafka Connector

The connector needs some configuration before it starts processing.  We issue a call to the connector's endpoint (through our load balanced service).

From your Cloud9 IDE, run this command, substituting the values for your S3 bucket name (visible as part of the output of the CDK stack), your AWS region, and your ALB endpoint (also visible in CDK output):

    curl -X POST \
        -H "Content-Type: application/json" \
        --data '{ "name": "s3-sink", "config": { "connector.class": "io.confluent.connect.s3.S3SinkConnector", "tasks.max": 1, "topics": "MyTopic", "s3.region": "<region>", "s3.bucket.name": "<bucket name>", "s3.part.size": 5242880, "flush.size": 3, "storage.class": "io.confluent.connect.s3.storage.S3Storage", "format.class": "io.confluent.connect.s3.format.json.JsonFormat", "schema.generator.class": "io.confluent.connect.storage.hive.schema.DefaultSchemaGenerator", "partitioner.class": "io.confluent.connect.storage.partitioner.DefaultPartitioner",  "schema.compatibility": "NONE" } }' \
    http://<ALB DNS>:8083/connectors

#### Verify S3 Sink is working

Look at the contents of your S3 bucket.  You should see files written into this bucket once the Sink is working.
