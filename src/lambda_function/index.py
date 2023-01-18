
import boto3
import json
import os
from botocore.exceptions import ClientError
from boto3.session import Session
from mfa import mfa

SECRETS_ID_LIST = [
  'sys1',
  'sys2'
]

def get_secret(secret_id):
    print('secretid:'+secret_id)
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_id
        )
    except ClientError as e:
        raise e
    secrets = get_secret_value_response['SecretString']
    return json.loads(secrets)

def create_client(secrets):
  access_key = secrets['access_key']
  secret_key = secrets['secret_key']

  client = boto3.client(
      's3',
      aws_access_key_id=access_key,
      aws_secret_access_key=secret_key
  )

  return client  

def create_mfa_client(secrets):
  access_key = secrets['access_key']
  secret_key = secrets['secret_key']
  mfa_secret = secrets['mfa_secret']
  mfa_device_arn = secrets['mfa_device']

  mfa_code = mfa.fetch_code(mfa_secret)

  sts_client = boto3.client(
    'sts',
      aws_access_key_id=access_key,
      aws_secret_access_key=secret_key  
  )

  sts_res = sts_client.get_session_token(
    DurationSeconds=3600,
    SerialNumber=mfa_device_arn,
    TokenCode=mfa_code['code']
  )

  cred = sts_res['Credentials']

  session = Session(
    aws_access_key_id=cred['AccessKeyId'],
    aws_secret_access_key=cred['SecretAccessKey'],
    aws_session_token=cred['SessionToken'],
    region_name='ap-northeast-1'
  )
  
  client = session.client('s3')

  return client

def exec_copy(event, client, dest_bucket, dest_prefix):
  bucket_name = event['Records'][0]['s3']['bucket']['name']
  from_key = event['Records'][0]['s3']['object']['key']
  file_name = os.path.basename(from_key)
  dest_full_prefix = os.path.join(dest_prefix, file_name)

  print(dest_full_prefix)
  print(f'Copying: from s3://{bucket_name}/{from_key} to s3://{dest_bucket}/{dest_full_prefix}')
  result = client.copy_object(
    Bucket=dest_bucket,
    Key=dest_full_prefix,
    CopySource={'Bucket': bucket_name, 'Key': from_key}
  )

  print(result)


def lambda_handler(event, context):
  for s in SECRETS_ID_LIST:
    secrets = get_secret(s)
    if secrets['mfa'] == 'TRUE':
      print('Create MFA client')
      client = create_mfa_client(secrets)
    else:
      print('Create not MFA client')
      client = create_client(secrets)
    print(client)
    exec_copy(event, client, secrets['bucket'], secrets['prefix'])
  
  return 200