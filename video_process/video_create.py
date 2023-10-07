import subprocess
import cv2
import numpy as np
import time
from PIL import Image
from helpers import setup_logger

def create_video(images_path, video_path):
    command = [
        'ffmpeg',
        '-framerate', '30',
        '-pattern_type', 'glob',
        '-i', f"{images_path}/*.png",
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        video_path
    ]
    process = subprocess.Popen(command, stderr=subprocess.PIPE, text=True)
    returncode = process.wait()  # Wait for the process to complete
    if returncode != 0:
        stderr_output = process.stderr.read()
        error_message = f'ffmpeg error: {stderr_output}'
        print(error_message)
        raise Exception(error_message)  # Raise an exception with the error output

def collect_and_write_images(output_image_queue, frame_extraction_complete, npz_extraction_complete, image_processing_complete, final_video_creation_complete, output_video_path):
    logger = setup_logger('2dto3dto2d:collect_and_write_images')
    images = []
    while True:
        if not output_image_queue.empty():
            frame_index, image_buf, write_to_file, fin_path = output_image_queue.get()
            
            if write_to_file:
                image = np.array(Image.open(fin_path))
            else:
                image = np.array(Image.open(image_buf))

            images.append((frame_index, image))
            logger.info(f"Collected image {frame_index}")
        elif frame_extraction_complete.is_set() and npz_extraction_complete.is_set() and image_processing_complete.set():
            break
        else:
            time.sleep(1)  # Wait for more images to be queued

    # Sort images by frame_index
    images.sort(key=lambda x: x[0])

    # Get image dimensions from the first image
    height, width, _ = images[0][1].shape

    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or use 'XVID'
    video = cv2.VideoWriter(output_video_path, fourcc, 30.0, (width, height))

    # Write images to video
    for _, image in images:
        video.write(image)

    video.release()
    logger.info(f"Video written to {output_video_path}")
    final_video_creation_complete.set()