import pickle
import os
import cv2
import shutil
import numpy as np
from tqdm import tqdm
from modules.hpe.hpe import HumanPoseEstimator
from utils.matplotlib_visualizer import MPLPosePrinter

from utils.params import MetrabsTRTConfig, RealSenseIntrinsics

in_dataset_path = "D:\\datasets\\nturgbd"
out_dataset_path = "D:\\datasets\\nturgbd_metrabs_2"
classes_path = "assets/nturgbd_classes.txt"
n = 16

VIS_DEBUG = False

if __name__ == "__main__":

    # raise Exception("REMOVE THIS LINE TO ERASE CURRENT DATASET")  # TODO ADD

    skeleton = 'smpl+head_30'
    with open('assets/skeleton_types.pkl', "rb") as input_file:
        skeleton_types = pickle.load(input_file)
    edges = skeleton_types[skeleton]['edges']

    model = HumanPoseEstimator(MetrabsTRTConfig(), RealSenseIntrinsics())
    if VIS_DEBUG:
        vis = MPLPosePrinter()  # TODO VIS DEBUG

    # Count total number of files (we remove 10 classes over 60 because those involves two person)
    total = int(sum([len(files) if '_s' in r else 0 for r, d, files in os.walk(in_dataset_path)]) * (1 - 16/60))

    # Get conversion class id -> class label
    with open(classes_path, "r", encoding='utf-8') as f:
        classes = f.readlines()
    class_dict = {}
    for c in classes:
        index, name, _ = c.split(".")
        name = name.strip().replace(" ", "_").replace("/", "-").replace("’", "")
        class_dict[index] = name

    # Create output directories (ONLY THE MISSING ONES)  # TODO CAREFUL, ERASE WHAT DONE BEFORE
    for value in list(class_dict.values())[60:]:
        shutil.rmtree(os.path.join(out_dataset_path, value))
        os.mkdir(os.path.join(out_dataset_path, value))

    # Iterate all videos
    with tqdm(total=total) as progress_bar:
        for root, dirs, files in os.walk(in_dataset_path):

            if '_s' not in root:
                continue

            for file in files:
                # Retrieve class name (between A and _ es 'S001C001P001R001A001_rgb.avi'
                class_id = int(file.split("A")[1].split("_")[0])  # take the integer of the class
                class_id = "A" + str(class_id)
                class_name = class_dict[class_id]

                # Skip if two person are involved
                if list(class_dict.keys()).index(class_id) >= 106:
                    continue

                # Check if output path already exists
                output_path = os.path.join(out_dataset_path, class_name)
                offset = sum([len(files) for r, d, files in os.walk(output_path)])
                output_path = os.path.join(output_path, str(offset) + '.pkl')

                # Read video
                full = os.path.join(root, file)
                video = cv2.VideoCapture(full)
                frames = []
                ret, frame = video.read()
                while ret:
                    frames.append(frame)
                    ret, frame = video.read()
                if len(frames) < n:
                    continue

                # Select just n frames
                n_frames = len(frames) - (len(frames) % n)
                if n_frames == 0:
                    continue
                indices = list(range(0, n_frames, int(n_frames / n)))
                frames = [frames[i] for i in indices]

                # Iterate over all frames
                poses = []
                res = np.zeros([30, 3])  # So if the first pose is none, there is no error

                for i, frame in enumerate(frames):
                    frame = frame[:, 240:-240, :]
                    frame = cv2.resize(frame, (640, 480))
                    new_res = model.estimate(frame)[0]
                    res = res if new_res is None else new_res
                    res = res - res[0]
                    poses.append(res)

                    if VIS_DEBUG:
                        cv2.imshow("", frame)  # TODO VIS DEBUG
                        vis.clear()  # TODO VIS DEBUG
                        vis.print_pose(res, edges)  # TODO VIS DEBUG
                        vis.sleep(0.01)  # TODO VIS DEBUG

                # Save result
                poses = np.array(poses)
                with open(output_path, "wb") as f:
                    pickle.dump(poses, f)
                assert (i+1) == n

                progress_bar.update()
