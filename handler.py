import json
import urllib.parse
import boto3
import subprocess
import os
import ffmpeg
import math

OUTPUT_BUCKET = "1229892289-stage-1"

s3 = boto3.client("s3")


def copy_folder_to_s3(local_folder_path, s3_bucket_name, s3_folder_name=None):
    s3 = boto3.client("s3")

    if s3_folder_name is None:
        s3_folder_name = os.path.basename(local_folder_path)

    for root, dirs, files in os.walk(local_folder_path):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_folder_path)
            s3_path = os.path.join(s3_folder_name, relative_path)

            try:
                s3.upload_file(local_path, s3_bucket_name, s3_path)
            except Exception as e:
                print(f"Error uploading {local_path}: {e}")


def getFilename(path):
    filename = os.path.basename(path)
    outdir = os.path.splitext(filename)[0]
    return outdir


def video_splitting_cmdline(video_filename):
    outdir = getFilename(video_filename)
    outdir = os.path.join("/tmp", outdir)
    output_dir = outdir
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    split_cmd = (
        "/usr/bin/ffmpeg -ss 0 -r 1 -i "
        + video_filename
        + " -vf fps=1/10 -start_number 0 -vframes 10 "
        + outdir
        + "/"
        + "output-%02d.jpg -y"
    )

    try:
        subprocess.check_call(split_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

    fps_cmd = (
        "ffmpeg -i " + video_filename + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    )
    fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    fps = math.ceil(float(fps))

    return outdir


def handler(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )

    download_path = os.path.join("/tmp", key)

    try:
        s3.download_file(bucket, key, download_path)

        output_path = video_splitting_cmdline(download_path)

        copy_folder_to_s3(output_path, OUTPUT_BUCKET, getFilename(download_path))

        return "Done"
    except Exception as e:
        raise e
