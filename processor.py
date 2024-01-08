
import base64
import os
import subprocess

tmp_frames_path = "inputs/tmp_frames"
restored_imgs_path = "results/restored_imgs"

class Result:
    def __init__(self, success=True, data=None, error=None):
        self.success = success
        self.data = data
        self.error = error

    def __repr__(self):
        return f"Result(success={self.success}, data={self.data}, error={self.error})"

def err(r):
    return f"ERROR: {r}"

def run(base_64, vid_path, vid_name="output_vid"):
    try:
        _delete_tmp()

        print("[GFPGAN] _decode_b64...")
        decode_result = _decode_b64(base_64, vid_path)
        if not decode_result.success:
            return err(decode_result)

        print(f"[GFPGAN] _split_vid_into_frames {vid_path}")
        frames_dir = _split_vid_into_frames(vid_path)
        if not frames_dir.success:
            return err(frames_dir)

        print(f"[GFPGAN] _gfpgan {frames_dir}")
        gan_result = _gfpgan(frames_dir.data)
        if not gan_result.success:
            return err(gan_result)

        print(f"[GFPGAN] _merge_frames_into_vid {gan_result.data} -> {vid_name}")
        output_vid = _merge_frames_into_vid(vid_path, vid_name)
        if not output_vid.success:
            return err(output_vid)

        print(f"[GFPGAN] DONE -> {output_vid}")

        result = _sanity_check_video(output_vid.data)
        print(f"[GFPGAN] vid sanity check: {result}")

        return output_vid.data
    except Exception as e:
        print(f"[GFPGAN] FAILED TO PROCESS DATA with exception: {e}")
        return err(e)


def _delete_tmp():
    _delete_contents(tmp_frames_path)
    _delete_contents(restored_imgs_path)
    os.makedirs(tmp_frames_path, exist_ok=True)
    os.makedirs(restored_imgs_path, exist_ok=True)

def _delete_contents(directory_path):
    try:
        import shutil
        shutil.rmtree(directory_path)
        print(f"Contents of {directory_path} deleted successfully.")
    except Exception as e:
        print(f"Failed to delete contents. Error deleting contents of {directory_path}: {e}")


def _decode_b64(base_64, out_path):
    try:
        directory = os.path.dirname(out_path)
        os.makedirs(directory, exist_ok=True)
        video_data = base64.b64decode(base_64)
        with open(out_path, 'wb') as output_file:
            output_file.write(video_data)
        return Result(data=out_path)
    except Exception as e:
        return Result(success=False, error=f"Error during _decode_b64: {e}")




def _split_vid_into_frames(input_video):
    out_dir = "inputs/tmp_frames"
    output_pattern = f"{out_dir}/frame%08d.jpg"
    ffmpeg_command = [
        'ffmpeg',
        "-hide_banner",
        "-loglevel", "error",
        '-i', input_video,
        '-qscale:v', '1',
        '-qmin', '1',
        '-qmax', '1',
        '-vsync', '0',
        output_pattern
    ]
    try:
        subprocess.run(ffmpeg_command, check=True)
        return Result(data=out_dir)
    except subprocess.CalledProcessError as e:
        return Result(success=False, error=f"Error during _split_vid_into_frames: {e}")


def _gfpgan(input_frames_dir):
    try:
        import restorer
        out_path = restorer.restore(input_frames_dir)
        return Result(data=out_path)
    except Exception as e:
        return Result(success=False, error=f"Error during restore: {e}")


def _merge_frames_into_vid(input_video, vid_name):
    input_pattern = "results/restored_imgs/frame%08d.jpg"
    out_dir = "results/vids"
    os.makedirs(out_dir, exist_ok=True)
    output_video = os.path.join(out_dir, f"{vid_name}.mp4")

    ffmpeg_command = [
        'ffmpeg',
        "-hide_banner",
        "-loglevel", "error",
        '-framerate', '30',
        '-i', input_pattern,
        '-i', input_video,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'copy', output_video
    ]
    try:
        subprocess.run(ffmpeg_command, check=True)
        return Result(data=output_video)
    except subprocess.CalledProcessError as e:
        return Result(success=False, data=f"Error during _merge_frames_into_vid: {e}")


def _sanity_check_video(file_path):
    try:
        # Run FFmpeg command to check video integrity
        command = [
            'ffmpeg',
            '-v', 'error',
            '-i', file_path,
            '-f', 'null', '-'
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Check if the output contains any error messages
        if 'error' in result.stderr.lower():
            return f"Error detected in video: {result.stderr}"
        else:
            return "Video is valid."

    except subprocess.CalledProcessError as e:
        return f"Error running FFmpeg command: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
