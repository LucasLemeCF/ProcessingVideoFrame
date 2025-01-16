import sys

sys.path.append('/opt/bin/')

import json
import os
import zipfile
import boto3
import pyshorteners
import requests
from botocore.exceptions import NoCredentialsError

s3_client = boto3.client('s3')
bucket_name = 'lucas-leme-teste'
email_sender = "videoframeprofiap@gmail.com"
email_api_key = "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"
url_smtp = "https://api.brevo.com/v3/smtp/email"

def lambda_handler(event, context):
    for message in event['Records']:
        response = process_message(message)

        if not response['statusCode'] in [200, 201, 202]:
            to_address = message['body']['to_address']
            send_email_error(to_address)
    
    return response

def process_message(message):
    body_message = message['body']

    try:
        response = process_frames(body_message)
    except Exception as err:
        print("An error occurred")
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
        
        send_email(to_address, url_download)

        return {
            'statusCode': 200,
            'body': json.dumps({ 
                'message': 'Processing completed successfully!'
            })
        }
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
        print(f"Downloaded {object_key} from S3 bucket {bucket_name}")
    except NoCredentialsError:
        print("Credentials not available")

def upload_to_s3(bucket_name, output_zip_key, file_path):
    try:
        s3_client.upload_file(file_path, bucket_name, output_zip_key)
        print(f"Uploaded {file_path} to S3 bucket {bucket_name}")
    except NoCredentialsError:
        print("Credentials not available")

def extract_frames(lambda_video_path, output_folder, frame_rate):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    os.system(f"/opt/bin/ffmpeg.exe -i {lambda_video_path} -vf fps=1/{frame_rate} {os.path.join(output_folder, 'frame_%04d.jpg')}")

def create_zip(output_folder, zip_path):
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(output_folder):
            for file in files:
                zipf.write(os.path.join(root, file), file)
    print(f"Created zip file {zip_path}")

def generate_url(bucket_name, object_key):
    expiration=3600
    try:
        response = s3_client.generate_presigned_url('get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration)
    except NoCredentialsError:
        print("Credentials not available")
        return None
    return response

def shorten_url(long_url):
    s = pyshorteners.Shortener()
    short_url = s.tinyurl.short(long_url)
    return short_url

def send_email(destinatario, url_download):
    headers = {
        "api-key": email_api_key,
        "Content-Type": "application/json"
    }

    data = {
        "sender": {"email": email_sender},
        "to": [{"email": destinatario}],
        "subject": "Video Frame Pro",
        "htmlContent": "<html><body><h1>Link para download do .zip: {}</h1></body></html>".format(url_download)
    }

    try:
        response = requests.post(url_smtp, headers=headers, json=data)

        if response.status_code in [202, 201]:
            print("✅ E-mail enviado com sucesso!")
        else:
            print(f"❌ Erro ao enviar o e-mail: {response.status_code}")
            print(response.text)

    except Exception as e:
        print("❌ Erro na requisição:", str(e))

def send_email_error(destinatario):
    headers = {
        "api-key": email_api_key,
        "Content-Type": "application/json"
    }

    data = {
        "sender": {"email": email_sender},
        "to": [{"email": destinatario}],
        "subject": "Video Frame Pro",
        "htmlContent": "<html><body><h1>Erro ao processar o video</h1></body></html>"
    }

    try:
        response = requests.post(url_smtp, headers=headers, json=data)

        if response.status_code in [202, 201]:
            print("✅ E-mail de erro enviado.")
        else:
            print(f"❌ Erro ao enviar o e-mail de erro: {response.status_code}")
            print(response.text)

    except Exception as e:
        print("❌ Erro na requisição:", str(e))