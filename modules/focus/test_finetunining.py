import cv2
import torch
from modules.focus.utils.misc import get_model
from modules.hpe.utils.misc import nms_cpu


if __name__ == "__main__":
    model = get_model()
    model.load_state_dict(torch.load('modules/focus/modules/raw/second.pth'))
    model.cuda()
    model.eval()
    cam = cv2.VideoCapture(0)

    while True:
        ret, img = cam.read()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        inp = torch.FloatTensor(img).cuda() / 255.
        inp = inp.permute(2, 0, 1)
        res = model([inp])
        boxes = res[0]['boxes'].detach().int().cpu().numpy()
        scores = res[0]['scores'].detach().cpu().numpy()
        good = nms_cpu(boxes, scores, nms_thresh=0.01)

        if len(good) > 0:
            boxes = boxes[good]
            scores = scores[good]
            good = scores > 0.8
            boxes = boxes[good]
            scores = scores[good]
            if len(boxes) > 0:
                for box in boxes:
                    img = cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)

        cv2.imshow("", img)
        cv2.waitKey(1)