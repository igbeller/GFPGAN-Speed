import multiprocessing
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import base64
import subprocess
import restorer

def process_data(input_queue):
    while True:
        data = input_queue.get()
        if data == 'STOP':
            break

        base_64 = "yaya"
        vid_path = "path"

        try:
            _decode_b64(base_64, vid_path)
            frames_dir = _split_vid_into_frames(vid_path)
            vid_path = _gfpgan(frames_dir)
            output_vid = _merge_frames_into_vid(vid_path)
            print(f"Processed output to : {output_vid}")

        except Exception as e:
            print(f"FAILED TO PROCESS DATA with exception: {e}")



def _decode_b64(base_64, out_path):
    try:
        video_data = base64.b64decode(base_64)
        with open(out_path, 'wb') as output_file:
            output_file.write(video_data)
        print(f"Conversion successful. MP4 file saved at {out_path}")
    except Exception as e:
        print(f"Error during conversion: {e}")


def _video_to_base64(file_path):
    try:
        with open(file_path, 'rb') as video_file:
            video_binary = video_file.read()
            base64_encoded = base64.b64encode(video_binary).decode('utf-8')
            return base64_encoded
    except Exception as e:
        print(f"Error: {e}")
        return None

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
    out_path = restorer.restore(input_frames_dir)
    return out_path

def _merge_frames_into_vid(input_video):
    input_pattern = "results/restored_imgs/frame%08d.jpg"
    output_video = "output_with_audio.mp4"
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



class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        print(f"self.path: {self.path}")
        print(f"self.path: {urlparse(self.path)}")
        print(f"query_components: {query_components}")
        data = query_components.get('data', [''])[0]
        queue_object = self.server.server_queue
        queue_object.put(data)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Data enqueued successfully")

    def do_POST(self):
        print(self.path)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        self.send_response(200)
        self.end_headers()
        print(post_data)
        self.wfile.write(b"Data posted? successfully")

def start_server(server_queue):
    server_address = ('localhost', 8080)
    http_server = HTTPServer(server_address, RequestHandler)
    http_server.server_queue = server_queue
    http_server.serve_forever()

if __name__ == '__main__':
    with multiprocessing.Manager() as manager:
        input_queue = manager.Queue()

        process = multiprocessing.Process(target=process_data, args=(input_queue,))
        process.start()

        server_process = multiprocessing.Process(target=start_server, args=(input_queue,))
        server_process.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            # Terminate the processing function and the server
            input_queue.put('STOP')
            process.join()
            server_process.terminate()
            server_process.join()
            print("Processes terminated.")
