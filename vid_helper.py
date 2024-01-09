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



# def merge_frames(img_folder, audio_file, output_file, fps=30, img_format="jpg"):
#     import imageio
#     from moviepy.editor import ImageSequenceClip, AudioFileClip
#     filex = f".{img_format}"
#     images = [imageio.v2.imread(os.path.join(img_folder, image)) for image in sorted(os.listdir(img_folder)) if image.endswith(filex)]
#     video_clip = ImageSequenceClip(images, fps=fps)
#     audio_clip = AudioFileClip(audio_file)
#     video_clip = video_clip.set_audio(audio_clip)
#     video_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")


def merge_frames_opencv(img_folder, audio_file, output_file, fps=30, img_format="jpg"):
    file_extension = f".{img_format}"

    image_files = [f for f in sorted(os.listdir(img_folder)) if f.endswith(file_extension)]

    first_image = cv2.imread(os.path.join(img_folder, image_files[0]))
    height, width, _ = first_image.shape

    base_name = os.path.basename(output_file).split(".")[0]

    # Specify the codec
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    tmp_output_file_writer = f"{base_name}_tmp_writer.mp4"
    video_writer = cv2.VideoWriter(tmp_output_file_writer, fourcc, fps, (width, height))

    for image_file in image_files:
        frame = cv2.imread(os.path.join(img_folder, image_file))
        video_writer.write(frame)

    video_writer.release()
    os.system(f"ffmpeg -i {tmp_output_file_writer} -i {audio_file} -pix_fmt yuv420p -c:v copy -c:a aac -strict experimental {base_name}_temp.mp4")
    os.rename(f"{base_name}_temp.mp4", output_file)
    os.remove(tmp_output_file_writer)


if __name__ == '__main__':
    # os.makedirs("pngs", exist_ok=True)
    # extract_frames("original.mp4", "pngs")
    # merge_frames_opencv("pngs", "original.mp4", "merged_pngs_result.mp4")
    pass