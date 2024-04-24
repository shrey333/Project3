import json
import urllib.parse
import boto3
import subprocess
import os
import math

OUTPUT_BUCKET = "1229892289-stage-1"

s3 = boto3.client("s3")

lambdaClient = boto3.client("lambda")


def copy_folder_to_s3(local_path, s3_bucket_name, s3_path):
    try:
        s3.upload_file(local_path, s3_bucket_name, s3_path)
    except Exception as e:
        print(f"Error uploading {local_path}: {e}")


def video_splitting_cmdline(video_filename):
    filename = os.path.basename(video_filename)
    outfile = os.path.splitext(filename)[0] + ".jpg"

    split_cmd = 'ffmpeg -y -i ' + video_filename + ' -vframes 1 ' + '/tmp/' + outfile
    try:
        subprocess.check_call(split_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

    fps_cmd = 'ffmpeg -y -i ' + video_filename + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    return outfile


def lambda_handler(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )

    download_path = os.path.join("/tmp", key)

    try:
        s3.download_file(bucket, key, download_path)

        output_path = video_splitting_cmdline(download_path)

        copy_folder_to_s3(f"/tmp/{output_path}", OUTPUT_BUCKET, output_path)
        
        lambdaClient.invoke(
            FunctionName="face-recognition", 
            InvocationType='Event', 
            Payload=json.dumps({
                "bucket_name": OUTPUT_BUCKET,
                "image_file_name": output_path
            })
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                "bucket_name": OUTPUT_BUCKET,
                "image_file_name": output_path
            })
        }
    except Exception as e:
        raise e