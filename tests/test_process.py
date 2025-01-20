import unittest
from unittest.mock import patch, MagicMock
import os
import json
from lambda_function import (
    lambda_handler,
    process_message,
    process_frames,
    download_from_s3,
    upload_to_s3,
    extract_frames,
    create_zip,
    generate_url,
    shorten_url,
    send_email,
    send_email_error
)
import boto3
from moto import mock_s3
import pyshorteners
import requests

class TestLambdaFunction(unittest.TestCase):

    @mock_s3
    @patch('lambda_function.s3_client')
    def test_download_from_s3(self, mock_s3_client):
        mock_s3_client.download_file.return_value = True
        download_from_s3('test-bucket', 'test-key', '/tmp/test-file')
        mock_s3_client.download_file.assert_called_with('test-bucket', 'test-key', '/tmp/test-file')

    @mock_s3
    @patch('lambda_function.s3_client')
    def test_upload_to_s3(self, mock_s3_client):
        mock_s3_client.upload_file.return_value = True
        upload_to_s3('test-bucket', 'test-key', '/tmp/test-file')
        mock_s3_client.upload_file.assert_called_with('/tmp/test-file', 'test-bucket', 'test-key')

    @patch('lambda_function.os.system')
    def test_extract_frames(self, mock_os_system):
        mock_os_system.return_value = 0
        extract_frames('/tmp/test-video', '/tmp/frames', 1)
        mock_os_system.assert_called_with('/opt/bin/ffmpeg.exe -i /tmp/test-video -vf fps=1/1 /tmp/frames/frame_%04d.jpg')

    def test_create_zip(self):
        os.makedirs('/tmp/frames', exist_ok=True)
        with open('/tmp/frames/test.jpg', 'w') as f:
            f.write("test")
        create_zip('/tmp/frames', '/tmp/test.zip')
        self.assertTrue(os.path.exists('/tmp/test.zip'))

    @patch('lambda_function.pyshorteners.Shortener')
    def test_shorten_url(self, MockShortener):
        mock_shortener = MockShortener.return_value
        mock_shortener.tinyurl.short.return_value = 'http://short.url'
        short_url = shorten_url('http://long.url')
        mock_shortener.tinyurl.short.assert_called_with('http://long.url')
        self.assertEqual(short_url, 'http://short.url')

    @patch('lambda_function.requests.post')
    def test_send_email(self, mock_post):
        mock_post.return_value = MagicMock(status_code=202)
        send_email('test@example.com', 'http://download.url')
        self.assertTrue(mock_post.called)

    @patch('lambda_function.requests.post')
    def test_send_email_error(self, mock_post):
        mock_post.return_value = MagicMock(status_code=202)
        send_email_error('test@example.com')
        self.assertTrue(mock_post.called)

    @patch('lambda_function.process_message')
    def test_lambda_handler(self, mock_process_message):
        mock_process_message.return_value = {'statusCode': 200}
        event = {
            'Records': [
                {
                    'body': {
                        'to_address': 'test@example.com',
                        'object_key': 'test-key',
                        'user_name': 'test-user',
                        'frame_rate': 1
                    }
                }
            ]
        }
        context = {}
        response = lambda_handler(event, context)
        mock_process_message.assert_called()
        self.assertEqual(response['statusCode'], 200)

    @patch('lambda_function.process_frames')
    def test_process_message(self, mock_process_frames):
        mock_process_frames.return_value = {'statusCode': 200}
        message = {
            'body': {
                'to_address': 'test@example.com',
                'object_key': 'test-key',
                'user_name': 'test-user',
                'frame_rate': 1
            }
        }
        response = process_message(message)
        mock_process_frames.assert_called()
        self.assertEqual(response['statusCode'], 200)

    @mock_s3
    @patch('lambda_function.s3_client')
    @patch('lambda_function.shorten_url')
    @patch('lambda_function.send_email')
    def test_process_frames(self, mock_send_email, mock_shorten_url, mock_s3_client):
        mock_s3_client.download_file.return_value = True
        mock_s3_client.upload_file.return_value = True
        mock_shorten_url.return_value = 'http://short.url'
        mock_send_email.return_value = True

        body_message = {
            'object_key': 'test-key',
            'user_name': 'test-user',
            'to_address': 'test@example.com',
            'frame_rate': 1
        }

        response = process_frames(body_message)
        self.assertEqual(response['statusCode'], 200)

if __name__ == '__main__':
    unittest.main()
