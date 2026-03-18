from flask import Flask, request, jsonify
import requests
import subprocess
import boto3
import os

app = Flask(__name__)

R2_ENDPOINT = os.environ["R2_ENDPOINT"]
R2_ACCESS_KEY = os.environ["R2_ACCESS_KEY"]
R2_SECRET_KEY = os.environ["R2_SECRET_KEY"]
R2_BUCKET = "india20sixty-videos"

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY
)

@app.route("/render", methods=["POST"])
def render():

    data = request.json

    images = data["images"]
    audio = data["audio"]
    job_id = data["job_id"]

    os.makedirs("temp", exist_ok=True)

    # download images
    image_files = []

    for i, url in enumerate(images):
        path = f"temp/img{i}.png"
        r = requests.get(url)
        open(path, "wb").write(r.content)
        image_files.append(path)

    # download audio
    audio_path = "temp/audio.mp3"
    r = requests.get(audio)
    open(audio_path, "wb").write(r.content)

    # create video
    video_path = "temp/output.mp4"

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-loop","1","-t","4","-i",image_files[0],
        "-loop","1","-t","5","-i",image_files[1],
        "-loop","1","-t","5","-i",image_files[2],
        "-loop","1","-t","6","-i",image_files[3],
        "-loop","1","-t","6","-i",image_files[4],
        "-i",audio_path,
        "-filter_complex",
        "[0:v][1:v][2:v][3:v][4:v]concat=n=5:v=1:a=0[outv]",
        "-map","[outv]",
        "-map","5:a",
        "-shortest",
        "-pix_fmt","yuv420p",
        video_path
    ]

    subprocess.run(ffmpeg_cmd)

    # upload to R2
    key = f"videos/{job_id}.mp4"

    s3.upload_file(video_path, R2_BUCKET, key)

    return jsonify({
        "video": key
    })


app.run(host="0.0.0.0", port=10000)
