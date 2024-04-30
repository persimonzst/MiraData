import tqdm
import os
import yt_dlp as youtube_dl
import argparse
import logging
import pandas as pd
import os, argparse
import tqdm
from moviepy.editor import VideoFileClip

parser = argparse.ArgumentParser()
parser.add_argument("--meta_csv", type=str,default="miradata_v0.csv")
parser.add_argument("--video_start_id", type=int,default=0)
parser.add_argument("--video_end_id", type=int,default=11000)
parser.add_argument("--raw_video_save_dir", type=str,default="miradata/raw_video")
parser.add_argument("--clip_video_save_dir", type=str,default="miradata/clip_video")
args = parser.parse_args()

# Check and create directories if they do not exist
if not os.path.exists(args.raw_video_save_dir):
    os.makedirs(args.raw_video_save_dir)
if not os.path.exists(args.clip_video_save_dir):
    os.makedirs(args.clip_video_save_dir)

encodings = ['ISO-8859-1', 'cp1252', 'utf-8']
# Try using different encoding formats
for encoding in encodings:
    try:
        df = pd.read_csv(args.meta_csv, encoding=encoding)
        print(f"Successfully loaded the csv file")
        break
    except UnicodeDecodeError:
        print(f"Error: {encoding} decoding failed, trying the next encoding format")

for i, row in tqdm.tqdm(df.iterrows()):
    video_name=row["index"].split("-")[0]
    video_download_path=os.path.join(args.raw_video_save_dir,
                                     str(int(video_name.split("_")[0])//1000).zfill(9),
                                     video_name+".mp4"
                                     )

    if os.path.exists(video_download_path):
        continue

    # download
    fail_times=0
    while True:
        try:
            video_id=row["video_id"]

            ydl_opts= {
            'format': '22', # mp4        1280x720   720p  550k , avc1.64001F, 24fps, mp4a.40.2@192k (44100Hz) (best)
            'continue_dl': True,
            'outtmpl': video_download_path,
            'external_downloader':'aria2c',
            'external_downloader_args': '-x 16 -k 1M',
            }
            ydl = youtube_dl.YoutubeDL(ydl_opts)
            ydl.download(
                [f'http://www.youtube.com/watch?v={video_id}'],
            )
            break

        except Exception as error:
            print(f"Download failed for video_id {video_id}, error: {str(error)}")
            logging.error(f"Download failed for video_id {video_id}, error: {str(error)}")
            fail_times += 1
            if fail_times >= 3:
                print(f"Failed 3 times for video_id {video_id}, skipping...")
                break

    # cut
    try:
        moviepy_video = VideoFileClip(video_download_path)

        clip_start=row["start_frame"]
        clip_end=row["end_frame"]
        clip_save_path=os.path.join(args.clip_video_save_dir,
                                     str(int(video_name.split("_")[0])//1000).zfill(9),
                                     row["index"]+".mp4"
                                     )

        clip = moviepy_video.subclip(clip_start / row["fps"], clip_end / row["fps"])

        if not os.path.exists(os.path.dirname(clip_save_path)):
            os.makedirs(os.path.dirname(clip_save_path))

        clip.write_videofile(clip_save_path)

    except Exception as error:
        print(f"Error cutting video {video_name}: {str(error)}")
        logging.error(f"Error cutting video {video_name}: {str(error)}")

print(f"Finish")
