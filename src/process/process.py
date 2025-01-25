import sys

sys.path.append('/opt/bin/')

import json
import os
import zipfile
import boto3
import pyshorteners
from botocore.exceptions import NoCredentialsError
import logging

s3_client = boto3.client('s3')
bucket_name = 'lucas-leme-teste'
sqs = boto3.client('sqs', region_name='us-east-1')
queue_url = 'https://sqs.us-east-1.amazonaws.com/440744219680/VideoFrameProSend'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    for message in event['Records']:
        response = process_message(message)

        logger.info(f"response: {response}")

        if not response['statusCode'] in [200, 201, 202]:
            to_address = message['body']['to_address']
            send_email_error(to_address)
    
    return response

def process_message(message):
    body_message = message['body']

    try:
        response = process_frames(body_message)
    except Exception as err:
        logger.info("An error occurred")
        raise err
    
    return response

def process_frames(body_message):
    object_key = body_message['object_key']
    user_name = body_message['user_name']
    to_address = body_message['to_address']
    frame_rate = body_message['frame_rate']

    download_path_bucket = f"entrada/{object_key}"
    lambda_video_path = f"/tmp/{object_key}"
    output_folder = "/tmp/frames"
    zip_path = "/tmp/frames.zip"
    output_zip_key = f"saida/{user_name}/{os.path.basename(zip_path)}"

    if frame_rate > 0:
        download_from_s3(bucket_name, download_path_bucket, lambda_video_path)
        extract_frames(lambda_video_path, output_folder, frame_rate)
        create_zip(output_folder, zip_path)
        upload_to_s3(bucket_name, output_zip_key, zip_path)

        long_url = generate_url(bucket_name, output_zip_key)
        url_download = shorten_url(long_url)

        logger.info(f"url_download: {url_download}")
        
        response = send_email_sucesso(to_address, url_download)

        return response
    else :
        return {
            'statusCode': 400,
            'body': json.dumps({ 
                'message': 'Invalid frame rate number, must be greater than 0'
            })
        }

def download_from_s3(bucket_name, object_key, download_path):
    try:
        s3_client.download_file(bucket_name, object_key, download_path)
        logger.info(f"Downloaded {object_key} from S3 bucket {bucket_name}")
    except NoCredentialsError:
        logger.info("Credentials not available")

def upload_to_s3(bucket_name, output_zip_key, file_path):
    try:
        s3_client.upload_file(file_path, bucket_name, output_zip_key)
        logger.info(f"Uploaded {file_path} to S3 bucket {bucket_name}")
    except NoCredentialsError:
        logger.info("Credentials not available")

def extract_frames(lambda_video_path, output_folder, frame_rate):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    os.system(f"/opt/bin/ffmpeg.exe -i {lambda_video_path} -vf fps=1/{frame_rate} {os.path.join(output_folder, 'frame_%04d.jpg')}")

def create_zip(output_folder, zip_path):
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(output_folder):
            for file in files:
                zipf.write(os.path.join(root, file), file)
    logger.info(f"Created zip file {zip_path}")

def generate_url(bucket_name, object_key):
    expiration=3600
    try:
        response = s3_client.generate_presigned_url('get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration)
    except NoCredentialsError:
        logger.info("Credentials not available")
        return None
    return response

def shorten_url(long_url):
    s = pyshorteners.Shortener()
    short_url = s.tinyurl.short(long_url)
    return short_url

def send_email_sucesso(to_address, url_download):
    message_body = { 
        "status": "sucesso", 
        "to_address": to_address,
        "url_download": url_download
    }

    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body)
    )

    logger.info(f"Body: {message_body}")

    return {
        'statusCode': 200,
        'body': json.dumps({ 
            'message': 'Processing completed successfully!'
        })
    }

def send_email_error(to_address):
    message_body = {
        "status": "erro",
        "to_address": to_address
    }

    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body)
    )

    logger.info(f"Body: {message_body}")

    return {
        'statusCode': 500,
        'body': json.dumps({ 
            'message': 'Error processing the frames'
        })
    }
