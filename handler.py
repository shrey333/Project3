import json
import boto3
import os
from face_recognition import face_recognition_function

s3 = boto3.client("s3")

OUTPUT_BUCKET = "1229892289-output"


def copy_folder_to_s3(local_path, s3_bucket_name, s3_path):
    try:
        s3.upload_file(local_path, s3_bucket_name, s3_path)
    except Exception as e:
        print(f"Error uploading {local_path}: {e}")


def handler(event, context):
    bucket_name = event["bucket_name"]
    image_file_name = event["image_file_name"]
    download_path = os.path.join("/tmp", image_file_name)

    try:
        s3.download_file(bucket_name, image_file_name, download_path)

        name = face_recognition_function(download_path)

        key = os.path.splitext(os.path.basename(download_path))[0].split(".")[0]

        copy_folder_to_s3(f"/tmp/{key}.txt", OUTPUT_BUCKET, f"{key}.txt")

        return {
            "statusCode": 200,
            "body": json.dumps({"name": name, "file_path": f"/tmp/{key}.txt"}),
        }
    except Exception as e:
        raise e
