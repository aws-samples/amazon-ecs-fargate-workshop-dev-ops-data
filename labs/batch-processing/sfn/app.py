# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

import boto3
import os
import xmltodict
import json 

# XML input file location in S3 is passed as an environment variable
BUCKET=os.environ['BUCKET']
S3PATH=os.environ['S3PATH']
print("Bucket: " + BUCKET)
print("S3 path: " + S3PATH)

# Local storage (volume mounted under /opt/data)
path_parts = os.path.split(S3PATH)
path_name = path_parts[1]
local_path = "/opt/data/{0}".format(path_name)
print("Local path: " + local_path)

# Download input file
s3 = boto3.client('s3')
s3.download_file(BUCKET, S3PATH, local_path)
print("Downloaded from s3")

# Convert to JSON
with open(local_path, 'rb') as input_file:
    output = json.dumps(xmltodict.parse(input_file), indent=4)
    print("Converted to JSON")

# Write file
output_path = local_path + ".json"
with open(output_path, 'w') as output_file:
    output_file.write(output)
    print("Wrote output")

# Upload to S3
s3.upload_file(output_path, BUCKET, S3PATH + ".json")
print("Uploaded to s3")
