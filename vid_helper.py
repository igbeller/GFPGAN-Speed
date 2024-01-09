import cv2
import os

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



def merge_frames(img_folder, audio_file, output_file, fps=30, img_format="jpg"):
    import imageio
    from moviepy.editor import ImageSequenceClip, AudioFileClip
    filex = f".{img_format}"
    images = [imageio.v2.imread(os.path.join(img_folder, image)) for image in sorted(os.listdir(img_folder)) if image.endswith(filex)]
    video_clip = ImageSequenceClip(images, fps=fps)
    audio_clip = AudioFileClip(audio_file)
    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")



if __name__ == '__main__':
    # extract_frames("original.mp4", "pngs")
    # merge_frames("pngs", "original.mp4", "merged_pngs_result.mp4")
    pass