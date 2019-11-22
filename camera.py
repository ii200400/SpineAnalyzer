# https://www.youtube.com/watch?v=tpWVyJqehG4&vl=ko 참고
import cv2
import dlib
# import numpy as np
import imutils
from imutils import face_utils
# import time
# import math
# import winsound


class ImageAnalyzer:
    # TODO 카메라 연결 상태에 따라서 필러그가 뽑혔을 때 다시 연결을 계속 시도해보도록 하려고 했는데 어렵다;;
    def __init__(self):
        # self.cam = cv2.VideoCapture(0)  # 카메라 지정
        self.cam = cv2.VideoCapture("./example.mp4")

        self.detector = dlib.get_frontal_face_detector()  # 얼굴인식 모델
        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")  # 얼굴 특징점 모델

        self.std_frame = None
        self.std_shape = None

        self.std_pose = []  # 기준 자세 리스트
        self.cur_pose = []  # 현재 자세 리스트
        # TODO 타이머는 view에서 하자.
        self.base_time = -1

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('!!')
        self.cam.release()
        # cv2.destroyAllWindows()

    # 이미지 존재여부와 이미지 자체와 이미지의 특징점을 반환하는 함수
    def faceDetect(self):
        ret, frame = self.cam.read()
        frame = imutils.resize(frame, width=400)

        # TODO ret이 언제 false가 되는지를 잘 모르겠다;
        # 카메라는 연결이 되어있는데 어떤 이유로 이미지를 불러오지 못하면 false가 나오기는 한다.
        if not ret:
            print('아이고..')
            return 0, (None, None)

        # 얼굴 인식
        faces = self.detector(frame)
        if len(faces) == 0:  # 인식되는 얼굴이 없는 경우
            return 1, (frame, None)

        # 첫번째로 인식되는 얼굴만 탐색
        face = faces[0]

        # 얼굴 특징점 인식
        shape = self.predictor(frame, face)
        shape = face_utils.shape_to_np(shape)
        return 2, (frame, shape)

    # 이미지에 특징점을 그리는 함수
    def drawPoints(self, frame, shape):
        # 특징점들의 그룹과 그룹의 범위
        for (name, (i, j)) in face_utils.FACIAL_LANDMARKS_IDXS.items():
            # 얼굴 특징점에 점 그리기
            for (x, y) in shape[i:j]:
                cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)

        return frame

    # 평균 점을 구하고 저장하는 함수
    def setPose(self, shape):
        avePoints = [[0, 0] for i in range(8)]

        # 특징점들의 그룹과 그룹의 범위
        for num, (name, (i, j)) in enumerate(imutils.face_utils.FACIAL_LANDMARKS_IDXS.items()):
            meanx, meany = 0, 0  # 평균을 저장할 변수
            count = 0

            # 얼굴 특징점 그룹의 위치 구하기
            for (x, y) in shape[i:j]:
                meanx += x
                meany += y
                count += 1

            meanx = int(meanx / count)
            meany = int(meany / count)
            avePoints[num][0], avePoints[num][1] = meanx, meany

        return avePoints

    # facedetect함수의 결과에 따라서 다른 이미지를 반환하는 함수 (메인 화면에서만 쓰인다.)
    def setFrame(self):
        status, (frame, shape) = self.faceDetect()
        if status == 0:
            return 0, None
        elif status == 1:
            self.std_frame = frame
            return 1, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif status == 2:
            self.std_frame, self.std_shape = frame, shape
            img = self.drawPoints(frame, shape)
            return 2, cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 기준 좌표 저장 (메세지 창에서만 쓰인다.)
    def setStandardPose(self):
        self.std_pose = self.setPose(self.std_shape)

    # 위의 함수를 이용하여 얼굴 점을 분석해 주는 것 ex 좋음 나쁨
    def FaceAnalyze(self):
        return
