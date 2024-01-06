
import base64
import os
import subprocess

tmp_frames_path = "inputs/tmp_frames"
restored_imgs_path = "results/restored_imgs"

def run(base_64, vid_path, vid_name="output_vid"):
    try:
        _delete_tmp()
        _decode_b64(base_64, vid_path)
        frames_dir = _split_vid_into_frames(vid_path)
        _gfpgan(frames_dir)
        output_vid = _merge_frames_into_vid(vid_path, vid_name)
        print(f"Processed output to : {output_vid}")
        return output_vid
    except Exception as e:
        print(f"FAILED TO PROCESS DATA with exception: {e}")
        return f"ERROR: {e}"


def _delete_tmp():
    _delete_contents(tmp_frames_path)
    _delete_contents(restored_imgs_path)

def _delete_contents(directory_path):
    try:
        import shutil
        shutil.rmtree(directory_path)
        print(f"Contents of {directory_path} deleted successfully.")
    except Exception as e:
        print(f"Error deleting contents of {directory_path}: {e}")


def _decode_b64(base_64, out_path):
    try:
        video_data = base64.b64decode(base_64)
        os.makedirs(out_path, exist_ok=True)
        with open(out_path, 'wb') as output_file:
            output_file.write(video_data)
        print(f"Conversion successful. file saved at {out_path}")
    except Exception as e:
        print(f"Error during conversion: {e}")




def _split_vid_into_frames(input_video):
    out_dir = "inputs/tmp_frames"
    output_pattern = f"{out_dir}/frame%08d.jpg"
    ffmpeg_command = [
        'ffmpeg',
        '-i', input_video,
        '-qscale:v', '1',
        '-qmin', '1',
        '-qmax', '1',
        '-vsync', '0',
        output_pattern
    ]
    try:
        subprocess.run(ffmpeg_command, check=True)
        print("Conversion successful.")
        return out_dir
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")


def _gfpgan(input_frames_dir):
    import restorer
    out_path = restorer.restore(input_frames_dir)
    return out_path

def _merge_frames_into_vid(input_video, vid_name):
    input_pattern = "results/restored_imgs/frame%08d.jpg"
    output_video = f"{vid_name}.mp4"
    ffmpeg_command = [
        'ffmpeg',
        '-framerate', '30',
        '-i', input_pattern,
        '-i', input_video,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'copy',
        output_video
    ]
    try:
        subprocess.run(ffmpeg_command, check=True)
        print("Conversion successful.")
        return output_video
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")