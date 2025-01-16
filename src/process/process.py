import json
import os
import zipfile

import boto3
import pyshorteners
import requests
from botocore.exceptions import NoCredentialsError

s3_client = boto3.client('s3')

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

def extract_frames(lambda_video_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    os.system(f"ffmpeg.exe -i {lambda_video_path} -vf fps=1/20 {os.path.join(output_folder, 'frame_%04d.jpg')}")

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
    # API Key do Brevo
    api_key = "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"
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }

    # Dados do e-mail
    data = {
        "sender": {"email": "videoframeprofiap@gmail.com"},
        "to": [{"email": destinatario}],
        "subject": "Video Frame Pro",
        "htmlContent": "<html><body><h1>Link para download do .zip: {}</h1></body></html>".format(url_download)
    }

    try:
        # Enviar o e-mail
        response = requests.post(url, headers=headers, json=data)

        # Imprimir detalhes da resposta para diagnóstico
        print("Código de status:", response.status_code)
        print("Resposta completa:", response.json())

        # Tratar status codes 202 e 201 como sucesso
        if response.status_code in [202, 201]:
            print("✅ E-mail enviado com sucesso!")
        else:
            print(f"❌ Erro ao enviar o e-mail: {response.status_code}")
            print(response.text)

    except Exception as e:
        print("❌ Erro na requisição:", str(e))

def lambda_handler(event, context):
    object_key = 'video_teste.mp4'
    user_name = 'lucas'
    to_address = 'lucasleme09@gmail.com'

    bucket_name = 'lucas-leme-teste'

    download_path_bucket = f"entrada/{object_key}"
    lambda_video_path = f"/tmp/{object_key}"
    output_folder = "/tmp/frames"
    zip_path = "/tmp/frames.zip"
    output_zip_key = f"saida/{user_name}/{os.path.basename(zip_path)}"

    download_from_s3(bucket_name, download_path_bucket, lambda_video_path)
    extract_frames(lambda_video_path, output_folder)
    create_zip(output_folder, zip_path)
    upload_to_s3(bucket_name, output_zip_key, zip_path)

    long_url = generate_url(bucket_name, output_zip_key)
    url_download = shorten_url(long_url)
    
    send_email(to_address, url_download)

    return {
        'statusCode': 200,
        'body': json.dumps({ 
            'message': 'Processing completed successfully!', 
            'public_url': url_download 
        })
    }

if __name__ == "__main__":
    lambda_handler()
