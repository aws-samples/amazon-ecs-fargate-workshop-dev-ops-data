# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_docdb as docdb,
    aws_msk as msk,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_s3 as s3,
    aws_servicediscovery as cloudmap,
    aws_events as events,
    aws_lambda as lambda_,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_transfer as transfer,
    aws_iam as iam,
    core
)
from typing import List


class FargateWorkshopDataengStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, subnets: List[str], vpc: ec2.IVpc, default_vpc_cidr_block: str, project: str, namespace: cloudmap.HttpNamespace, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # firewall for load balancers
        self.lbFirewall = ec2.SecurityGroup(
                scope = self,
                id = 'LbFirewall',
                vpc = vpc,
                description = 'Load balancer firewall'
        )
        self.lbFirewall.add_ingress_rule(
                peer = ec2.Peer.ipv4(vpc.vpc_cidr_block),
                connection = ec2.Port.all_traffic()
        )
        self.lbFirewall.add_ingress_rule(
                peer = ec2.Peer.ipv4(default_vpc_cidr_block),
                connection = ec2.Port.all_traffic()
        )

        # unified client firewall for both MSK and DocumentDB
        self.unifiedClientFirewall = ec2.SecurityGroup(
                scope = self,
                id = 'UnifiedClientFirewall',
                vpc = vpc,
                description = 'Client access firewall for DocumentDB and MSK'
        )
        self.unifiedClientFirewall.add_ingress_rule(
                peer = self.lbFirewall,
                connection = ec2.Port.all_traffic()
        )

        # DocumentDB cluster
        projTag = core.CfnTag(key = 'Project', value = project)
        subnetGroup = docdb.CfnDBSubnetGroup(
                scope = self,
                id = 'DatabaseSubnetGroup',
                db_subnet_group_description = 'Subnet group for database',
                subnet_ids = subnets,
                tags = [projTag, core.CfnTag(key = 'Name', value = 'DocDbSubnetGroup')]
        )

        self.clientFirewall = ec2.SecurityGroup(
                scope = self,
                id = 'DatabaseClientFirewall',
                vpc = vpc,
                description = 'Client access firewall for DocumentDB'
        )
        self.dbFirewall = ec2.SecurityGroup(
                scope = self,
                id = 'DatabaseInternalFirewall',
                vpc = vpc,
                allow_all_outbound = True,
                description = 'Firewall for DocumentDB'
        )
        self.dbFirewall.add_ingress_rule(
                peer = self.clientFirewall,
                connection = ec2.Port.all_traffic()
        )
        self.dbFirewall.add_ingress_rule(
                peer = self.unifiedClientFirewall,
                connection = ec2.Port.all_traffic()
        )
        self.dbFirewall.add_ingress_rule(
                peer = ec2.Peer.ipv4(default_vpc_cidr_block),
                connection = ec2.Port.all_traffic()
        )
        self.docdbCluster = docdb.CfnDBCluster(
                scope=self,
                id='DataStore',
                db_subnet_group_name = subnetGroup.ref,
                master_username = 'DocDbMaster',
                master_user_password = 'DocDbPass',
                vpc_security_group_ids = [self.dbFirewall.security_group_id]
        )
        self.docdbInstances = [
                docdb.CfnDBInstance(
                    scope = self,
                    id="DataStore-Instance-{0}".format(str(i)),
                    db_cluster_identifier = self.docdbCluster.ref,
                    db_instance_class = 'db.r5.xlarge'
                )
                for i in range(3)
        ]
        self.docdbCloudMap = namespace.create_service(
                id = 'DbSvc'
        )
        self.docdbCloudMap.register_non_ip_instance(
                id = 'dbEndpoint',
                custom_attributes = { 'endpoint': self.docdbCluster.attr_endpoint, 'user': 'DocDbMaster', 'password': 'DocDbPass'}
        )
        self.docdbCloudMap.register_non_ip_instance(
                id = 'dbReadEndpoint',
                custom_attributes = { 'endpoint': self.docdbCluster.attr_read_endpoint }
        )

        # MSK cluster
        self.kafkaClientFirewall = ec2.SecurityGroup(
                scope = self,
                id = 'KafkaClientFirewall',
                vpc = vpc,
                description = 'Client access firewall for Kafka'
        )
        self.kafkaFirewall = ec2.SecurityGroup(
                scope = self,
                id = 'KafkaInternalFirewall',
                vpc = vpc,
                allow_all_outbound = True,
                description = 'Firewall for Kafka'
        )
        self.kafkaFirewall.add_ingress_rule(
                peer = self.kafkaClientFirewall,
                connection = ec2.Port.all_traffic()
        )
        self.kafkaFirewall.add_ingress_rule(
                peer = self.unifiedClientFirewall,
                connection = ec2.Port.all_traffic()
        )
        self.kafkaFirewall.add_ingress_rule(
                peer = ec2.Peer.ipv4(default_vpc_cidr_block),
                connection = ec2.Port.all_traffic()
        )
        self.kafkaFirewall.add_ingress_rule(
                peer = self.kafkaFirewall,
                connection = ec2.Port.all_traffic()
        )
        num_brokers = len(subnets)
        if num_brokers < 3:
            num_brokers = 2 * num_brokers
        self.kafka = msk.CfnCluster(
                scope = self,
                id = 'kafka',
                cluster_name = 'kafkafargateworkshop',
                kafka_version = '2.2.1',
                number_of_broker_nodes = num_brokers,
                enhanced_monitoring = 'PER_TOPIC_PER_BROKER',
                broker_node_group_info = msk.CfnCluster.BrokerNodeGroupInfoProperty(
                    client_subnets = subnets,
                    instance_type = 'kafka.m5.large',
                    security_groups = [self.kafkaFirewall.security_group_id]
                )
        )
        self.kafkaCloudMap = namespace.create_service(
                id = 'KafkaSvc'
        )
        self.kafkaCloudMap.register_non_ip_instance(
                id = 'KafkaBrokerArn',
                custom_attributes = { 'broker_arn': self.kafka.ref }
        )

        # ECR
        self.docker_repo = ecr.Repository(
                scope = self, 
                id = "FargateImageRepository"
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamRegion',
                string_value = self.region,
                parameter_name = 'region'
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamRepoUri',
                string_value = self.docker_repo.repository_uri,
                parameter_name = 'repo_uri'
        )
        self.docker_repo_s3sink = ecr.Repository(
                scope = self, 
                id = "FargateImageRepositoryS3Sink"
        )
        self.docker_repo_s3sinkhc = ecr.Repository(
                scope = self, 
                id = "FargateImageRepositoryS3SinkHC"
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamRepoUriS3Sink',
                string_value = self.docker_repo_s3sink.repository_uri,
                parameter_name = 'repo_uri_s3_sink'
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamRepoUriS3SinkHC',
                string_value = self.docker_repo_s3sinkhc.repository_uri,
                parameter_name = 'repo_uri_s3_sink_hc'
        )
        self.docker_repo_sftp = ecr.Repository(
                scope = self, 
                id = "FargateImageRepositorySftp"
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamRepoUriSftp',
                string_value = self.docker_repo_sftp.repository_uri,
                parameter_name = 'repo_uri_sftp'
        )
        self.docker_repo_batch = ecr.Repository(
                scope = self, 
                id = "FargateImageRepositoryBatch"
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamRepoUriBatch',
                string_value = self.docker_repo_batch.repository_uri,
                parameter_name = 'repo_uri_batch'
        )

        # SFTP server
        self.sftpBucket = s3.Bucket(
                scope = self, 
                id = "SFTPBucket", 
                block_public_access = s3.BlockPublicAccess.BLOCK_ALL,
                encryption = s3.BucketEncryption.S3_MANAGED
        )
        core.CfnOutput(
            scope = self, 
            id = "SFTPBucketName",
            value=self.sftpBucket.bucket_name
        )
        self.sftp_role = iam.Role(
                scope = self, 
                id = "SFTPRole",
                assumed_by=iam.ServicePrincipal("transfer.amazonaws.com")
        )
        self.sftp_role.add_to_policy(
                statement = iam.PolicyStatement(
                    resources = [self.sftpBucket.bucket_arn, self.sftpBucket.bucket_arn + '/*'],
                    actions = ['s3:*']
                )
        )
        self.sftp_vpce = vpc.add_interface_endpoint(id = "SftpEndpoint", service = ec2.InterfaceVpcEndpointAwsService.TRANSFER )
        self.sftp_vpce.connections.allow_default_port_from(other = ec2.Peer.ipv4(vpc.vpc_cidr_block))
        self.sftp_vpce.connections.allow_default_port_from(other = ec2.Peer.ipv4(default_vpc_cidr_block))
        self.sftp_vpce.connections.allow_from(other = ec2.Peer.ipv4(vpc.vpc_cidr_block), port_range = ec2.Port.tcp(22))
        self.sftp_vpce.connections.allow_from(other = ec2.Peer.ipv4(default_vpc_cidr_block), port_range = ec2.Port.tcp(22))
        self.sftp = transfer.CfnServer(
                scope = self,
                id = "SFTP",
                endpoint_type = 'VPC_ENDPOINT',
                endpoint_details = transfer.CfnServer.EndpointDetailsProperty(vpc_endpoint_id = self.sftp_vpce.vpc_endpoint_id),
                identity_provider_type = 'SERVICE_MANAGED'
        )
        self.sftp_user = transfer.CfnUser(
                scope = self,
                id = "SFTPUser",
                role = self.sftp_role.role_arn,
                server_id = self.sftp.attr_server_id,
                user_name = "sftpuser"
        )
        core.CfnOutput(
            scope = self, 
            id = "SFTPHostVpceOut",
            value=self.sftp_vpce.vpc_endpoint_id
        )
        core.CfnOutput(
            scope = self, 
            id = "SFTPUserOut",
            value=self.sftp_user.attr_user_name
        )
        self.sftpCloudMap = namespace.create_service(
                id = 'SftpSvc',
                name = 'SFTP'
        )
        self.sftpCloudMap.register_non_ip_instance(
                id = 'sftpEndpoint',
                custom_attributes = { 'vpce_id': self.sftp_vpce.vpc_endpoint_id, 'user': 'sftpuser', 'bucket': self.sftpBucket.bucket_name}
        )
