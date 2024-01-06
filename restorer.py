import cv2
import glob
import os
import torch
from basicsr.utils import imwrite
from gfpgan import GFPGANer

bg_upsampler = None

upscale = 1
arch = 'clean'
channel_multiplier = 2
model_name = 'GFPGANv1.3'
url = 'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth'

# determine model paths
model_path = os.path.join('experiments/pretrained_models', model_name + '.pth')
if not os.path.isfile(model_path):
    model_path = os.path.join('gfpgan/weights', model_name + '.pth')
if not os.path.isfile(model_path):
    # download pre-trained models from url
    model_path = url
restorer = GFPGANer(
    model_path=model_path,
    upscale=upscale,
    arch=arch,
    channel_multiplier=channel_multiplier,
    bg_upsampler=bg_upsampler)


RESTORED_DIR_NAMME = "restored_imgs"

def restore(arg_input="inputs/tmp_frames", output_dir="results"):
    """Inference demo for GFPGAN (for users).
    """
    global restorer

    # ------------------------ input & output ------------------------
    if arg_input.endswith('/'):
        arg_input = arg_input[:-1]
    if os.path.isfile(arg_input):
        img_list = [arg_input]
    else:
        img_list = sorted(glob.glob(os.path.join(arg_input, '*')))

    os.makedirs(output_dir, exist_ok=True)

    # ------------------------ restore ------------------------
    ctx = torch.multiprocessing.get_context("spawn")
    pool = ctx.Pool(7)
    pool.map(restore_mul, img_list)

    return os.path.join(output_dir, RESTORED_DIR_NAMME)


def restore_mul(img_path, output_dir, arg_ext="auto", weight=0.5, only_center_face=False, aligned=False):
        # read image
        img_name = os.path.basename(img_path)
        print(f'Processing {img_name} ...')
        basename, ext = os.path.splitext(img_name)
        input_img = cv2.imread(img_path, cv2.IMREAD_COLOR)

        # restore faces and background if necessary
        cropped_faces, restored_faces, restored_img = restorer.enhance(
            input_img,
            has_aligned=aligned,
            only_center_face=only_center_face,
            paste_back=True,
            weight=weight)
        # save restored img
        if restored_img is not None:
            if arg_ext == 'auto':
                extension = ext[1:]
            else:
                extension = arg_ext

            save_restore_path = os.path.join(output_dir, RESTORED_DIR_NAMME, f'{basename}.{extension}')
            imwrite(restored_img, save_restore_path)






