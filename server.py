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
    print(f"GFPGAN start process_data")
    while True:
        data = input_queue.get()
        if data == STOP:
            break

        base_64 = data["base64"]
        gan_id = data[KEY_ID]
        vid_path = os.path.join("inputs/vids", f"{gan_id}.mp4")
        os.makedirs("inputs/vids", exist_ok=True)

        import processor
        out_path = processor.run(base_64, vid_path, vid_name=gan_id)

        if "ERROR:" in out_path:
            os.makedirs(ERR_DIR, exist_ok=True)
            _write_error_to_file(f"{gan_id} {out_path}", _err_file_path(gan_id))
            print(f"ERROR id: {gan_id} wrote error: {out_path} to {_err_file_path(gan_id)}")
        else:
            print(f"id: {gan_id} processed to: {out_path}")



def _errfn(gan_id):
    return f"error_{gan_id}.txt"


ERR_DIR = "errors"


def _err_file_path(gan_id):
    return os.path.join(ERR_DIR, _errfn(gan_id))


def _write_error_to_file(error_message, err_file_path):
    try:
        with open(err_file_path, "w") as error_file:
            error_file.write(error_message)

    except Exception as e:
        print(f"Failed to write to error file {err_file_path}: {e}")


def _file_to_urlsafe_base64(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_binary = file.read()
            print(f"_file_to_urlsafe_base64 {file_path} -> binary len: {len(file_binary)}")
            base64_encoded = base64.urlsafe_b64encode(file_binary)
            print(f"_file_to_urlsafe_base64 {file_path} -> encoded bytes len: {len(base64_encoded)}")
            return base64_encoded.decode(ENCODING)
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

        print(f"post request, gan_id: {json_data[KEY_ID]}")

        self.server.server_queue.put(json_data)
        self.respond(200, {KEY_ID: json_data[KEY_ID]})


    def respond(self, code, json_content):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        response_json = json.dumps(json_content)
        self.wfile.write(bytes(response_json, ENCODING))

    def handle_get(self):
        if "/get/" in self.path:
            return self._get_gan_output(self.path.split("/")[-1])
        return {"get": "hi"}

    def _get_gan_output(self, gan_id):
        file_path = os.path.join("results/vids", f"{gan_id}.mp4")

        err_path = _err_file_path(gan_id)
        if os.path.exists(err_path):
            with open(err_path, 'r') as file:
                content = file.read()
                print(f"return error: {content}")
                return {KEY_ID: gan_id, "error": content}

        if not os.path.exists(file_path):
            return {KEY_ID: gan_id}
        else:
            base64str = _file_to_urlsafe_base64(file_path)
            if "ERROR" in base64str:
                return {KEY_ID: gan_id, "error": base64str}
            else:
                return {
                        KEY_ID: gan_id,
                        "base64": base64str,
                        # "restored_frame": _get_restored_img()
                    }

    def _err(self, content):
        return {"error": content}


def _get_restored_img():
    path = "results/restored_imgs/frame00000005.jpg"
    if os.path.exists(path):
        return _file_to_urlsafe_base64(path)
    else:
        return None

def start_server(server_queue):
    server_address = ('127.0.0.1', 8080)
    print(f"GFPGAN start_server on {server_address}")
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
