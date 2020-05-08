# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

import boto3
import os
import paramiko
import traceback
import io
import base64
from botocore.exceptions import ClientError

def create_sftp_client(host, port, username, password, keyfiledata, keyfiletype):
    sftp = None
    key = None
    transport = None
    try:
        if keyfiledata is not None:
            # Get private key used to authenticate user.
            keyfile = io.StringIO(keyfiledata)
            if keyfiletype == 'DSA':
                # The private key is a DSA type key.
                key = paramiko.DSSKey.from_private_key(keyfile)
            else:
                # The private key is a RSA type key.
                key = paramiko.RSAKey.from_private_key(keyfile)

        # Create Transport object using supplied method of authentication.
        transport = paramiko.Transport((host, port))
        transport.connect(None, username, password, key)

        sftp = paramiko.SFTPClient.from_transport(transport)

        return sftp
    except Exception as e:
        print('An error occurred creating SFTP client: %s: %s' % (e.__class__, e))
        traceback.print_exc()
        if sftp is not None:
            sftp.close()
        if transport is not None:
            transport.close()
        pass

# Look up SFTP server
print("Looking up SFTP information")
svc_client = boto3.client('servicediscovery')
response = svc_client.discover_instances(
    NamespaceName='FargateWorkshopNamespace',
    ServiceName='SFTP'
)
sftp_vpce_id = response['Instances'][0]['Attributes']['vpce_id']
sftp_user = response['Instances'][0]['Attributes']['user']
sftp_bucket = response['Instances'][0]['Attributes']['bucket']

# Look up VPC endpoint
ec2_client = boto3.client('ec2')
response = ec2_client.describe_vpc_endpoints(DryRun = False, VpcEndpointIds = [sftp_vpce_id])
sftp_host = response['VpcEndpoints'][0]['DnsEntries'][0]['DnsName']
print("Got SFTP host {0} and user {1}".format(sftp_host, sftp_user))

# Look up SSH key
secret_name = "sftpkey"
sm_client = boto3.client('secretsmanager')
get_secret_value_response = sm_client.get_secret_value( SecretId=secret_name)
keyfiledata = get_secret_value_response['SecretString']

# Connect
sftp = create_sftp_client(sftp_host, 22, sftp_user, '', keyfiledata, keyfiletype = 'RSA')

# List files
filepath = "/" + sftp_bucket 
remote_files = sftp.listdir(path=filepath)
for r in remote_files:
    print("Found file " + r)

# Close
if sftp: sftp.close()
