
import base64
import os
import shutil
import subprocess
import vid_helper

TMP_FRAMES_DIR = "inputs/tmp_frames"
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

        result = _sanity_check_video(output_vid.data)
        print(f"[GFPGAN] vid sanity check: {result}")

        if result == "Video is valid.":
            os.makedirs("results/vids", exist_ok=True)
            shutil.move(output_vid.data, "results/vids")

        print(f"[GFPGAN] DONE -> {output_vid}")
        return output_vid.data
    except Exception as e:
        print(f"[GFPGAN] FAILED TO PROCESS DATA with exception: {e}")
        return err(e)


def _delete_tmp():
    _delete_contents(TMP_FRAMES_DIR)
    _delete_contents(restored_imgs_path)
    os.makedirs(TMP_FRAMES_DIR, exist_ok=True)
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
    try:
        out_folder = vid_helper.extract_frames(input_video, TMP_FRAMES_DIR, target_fps=30)
        if out_folder is None:
            return Result(success=False, error=f"_split_vid_into_frames: couldn't open video file")
        return Result(data=out_folder)
    except Exception as e:
        return Result(success=False, error=f"Error during _split_vid_into_frames: {e}")


def _split_vid_into_frames_ffmpeg(input_video):
    out_dir = TMP_FRAMES_DIR
    output_pattern = f"{out_dir}/frame%08d.jpg"
    ffmpeg_command = [
        'ffmpeg',
        "-hide_banner",
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



TMP_OUT_DIR = "results/tmp_vids"


def _get_out_vid_path(vid_name):
    return os.path.join(TMP_OUT_DIR, f"{vid_name}.mp4")


def _merge_frames_into_vid(audio_ref_video, vid_name):
    try:
        os.makedirs(TMP_OUT_DIR, exist_ok=True)
        output_video = _get_out_vid_path(vid_name)
        vid_helper.merge_frames("results/restored_imgs", audio_ref_video, output_video)
        return Result(data=output_video)
    except subprocess.CalledProcessError as e:
        return Result(success=False, data=f"Error during _merge_frames_into_vid: {e}")


def _merge_frames_into_vid_ffmpeg(input_video, vid_name):
    input_pattern = "results/restored_imgs/frame%08d.jpg"
    os.makedirs(TMP_OUT_DIR, exist_ok=True)
    output_video = _get_out_vid_path(vid_name)

    ffmpeg_command = [
        'ffmpeg',
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


