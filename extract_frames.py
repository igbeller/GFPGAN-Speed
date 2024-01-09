import cv2

def extract_frames(input_video, output_folder, target_fps=None):
    cap = cv2.VideoCapture(input_video)

    if not cap.isOpened():
        print("Error: Couldn't open the video file.")
        return None

    if target_fps is not None:
        cap.set(cv2.CAP_PROP_FPS, target_fps)

    _fps = int(cap.get(cv2.CAP_PROP_FPS))
    _width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    _height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    import os
    os.makedirs(output_folder, exist_ok=True)

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_path = os.path.join(output_folder, f"frame{frame_count:08d}.jpg")
        cv2.imwrite(frame_path, frame)

        frame_count += 1

    cap.release()
    return output_folder



if __name__ == '__main__':
    # extract_frames("original.mp4", "pngs")
    pass