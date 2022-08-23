import boto3
import os
from botocore.exceptions import ClientError


def send_file(file, key):
    client = boto3.client('s3')

    client.put_object(
        Body=file.getvalue(),
        Bucket=os.environ.get('AWS_STORAGE_BUCKET_NAME'),
        Key=key
    )


def check_path(path):
    client = boto3.client('s3')
    try:
        client.head_object(Bucket=os.environ.get('AWS_STORAGE_BUCKET_NAME'), Key=path)
    except ClientError as e:
        return int(e.response['Error']['Code']) != 404
    return True


def delete_file(path):
    client = boto3.client('s3')

    client.delete_object(
        Bucket=os.environ.get('AWS_STORAGE_BUCKET_NAME'),
        Key=path
    )
