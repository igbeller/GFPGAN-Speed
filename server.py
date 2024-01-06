import multiprocessing
import os.path
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import uuid
import base64

# workflow: "img" or "vid"

'''
{
    "workflow" : "img",
    "base64" : "<string>",
    "weight" : 0.5,
    "only_center_face": false,
    "aligned": false
}
'''

KEY_ID = "gan_id"
ENCODING = 'utf-8'

STOP = "STOP"

def process_data(input_queue):
    while True:
        data = input_queue.get()
        if data == STOP:
            break
        print(f"data: {data}")
        base_64 = data["base64"]
        gan_id = data[KEY_ID]
        vid_path = os.path.join("inputs/vids", f"{gan_id}.mp4")
        import processor
        out_path = processor.run(base_64, vid_path, vid_name=gan_id)
        print(f"id: {id} processed to: {out_path}")



def _video_to_base64(file_path):
    try:
        with open(file_path, 'rb') as video_file:
            video_binary = video_file.read()
            base64_encoded = base64.b64encode(video_binary).decode(ENCODING)
            return base64_encoded
    except Exception as e:
        print(f"Error: {e}")
        return None


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.respond(200, self.handle_get())
        except Exception as e:
            self.respond(400, self._err(f"smth went wrong {e}"))
        return

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            json_data = json.loads(post_data.decode(ENCODING))
        except Exception as e:
            self.respond(422, self._err(f"post data not a json. e: {e}"))
            return

        json_data[KEY_ID] = str(uuid.uuid4())

        self.server.server_queue.put(json_data)
        self.respond(200, {KEY_ID: json_data[KEY_ID]})


    def respond(self, code, json_content):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        response_json = json.dumps(json_content)
        self.wfile.write(bytes(response_json, ENCODING))

    def handle_get(self):
        print(f"get: {self.path}")
        if "/get/" in self.path:
            return self._get_gan_output(self.path.split("/")[-1])
        return {"get": "hi"}

    def _get_gan_output(self, gan_id):
        file_path = os.path.join("results", gan_id)
        if not os.path.exists(file_path):
            return {KEY_ID: gan_id}
        else:
            base64str = _video_to_base64(file_path)
            if "ERROR" in base64str:
                return {KEY_ID: gan_id, "error": base64str}
            else:
                return {KEY_ID: gan_id, "base64": base64str}

    def _err(self, content):
        return {"error": content}



def start_server(server_queue):
    server_address = ('127.0.0.1', 8080)
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
            input_queue.put(STOP)
            process.join()
            server_process.terminate()
            server_process.join()
            print("Server terminated.")
