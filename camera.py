# https://www.youtube.com/watch?v=tpWVyJqehG4&vl=ko 참고
import cv2
import dlib
import numpy as np


def ImageDownScale(img):
    # 이미지 크기 조절
    width = len(img[0])
    height = len(img)
    if width > height:
        long = width
    else:
        long = height

    if long > 750:
        rate = 750 / long
        img = cv2.resize(img, dsize=(0, 0), fx=rate, fy=rate, interpolation=cv2.INTER_AREA)

    return img


class ImageDetection:
    #TODO 카메라 연결 상태에 따라서 필러그가 뽑혔을 때 다시 연결을 계속 시도해보도록 하려고 했는데 어렵다;;
    def __init__(self):
        # 캠 열기
        self.cam = cv2.VideoCapture(0)
        # 이미지 저장
        # self.img = None
        # 얼굴 인식용 오브젝트 생성(얼굴 인식 모델 사용)
        self.detector = dlib.get_frontal_face_detector()
        # 인식된 얼굴의 특징점을 찾는 오브젝트 생성(머신러닝으로 학습된 모델이라고 한다.)
        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(6)
        self.cam.release()
        # cv2.destroyAllWindows()

    def FaceDetect(self):
        ret, img = self.cam.read()
        # self.img = img

        #TODO ret이 언제 false가 되는지를 잘 모르겠다;
        # 카메라는 연결이 되어있는데 어떤 이유로 이미지를 불러오지 못하면 false가 나오기는 한다.
        if not ret:
            print('아이고..')
            return False

        img = ImageDownScale(img)

        # 얼굴 인식
        copy2 = img.copy()
        faces = self.detector(copy2)
        if len(faces) == 0:
            # cv2.imshow("Face", copy2)
            return cv2.cvtColor(copy2, cv2.COLOR_BGR2RGB)
        face = faces[0]

        ##얼굴 위치를 시각화(사각형) 및 얼굴 이미지 생성
        cv2.rectangle(copy2, pt1=(face.left(), face.top())
                      , pt2=(face.right(), face.bottom()), color=(255, 255, 255)
                      , thickness=2, lineType=cv2.LINE_AA)

        # 얼굴 인식
        dlib_shape = self.predictor(copy2, face)
        eye_sum = np.array([0, 0], dtype=int)  # 눈 위치 저장할 변수

        l_height = -1
        # 얼굴의 각 부분을 점으로 시각화(원)
        for p in dlib_shape.parts():
            cv2.circle(copy2, center=tuple(np.array([p.x, p.y])), radius=1
                       , color=(0, 255, 255), thickness=2, lineType=cv2.LINE_AA)
            if l_height == -1:
                l_height = p.y
            elif l_height < p.y:
                l_height = p.y

        ##        count=0                                 #평균을 구하기 위한 count
        ##        cv2.line(copy2, (0,l_height),(1000,l_height),color=(0, 255, 255),thickness = 2)
        ##
        ##            eye_sum+=np.array([p.x,p.y])
        ##            count+=1
        ##        eye_ave = np.int64(eye_sum/count)       #얼굴에 관한 array들의 평균

        ##        얼굴의 중심점을 점으로 시각화(원)
        ##        cv2.circle(copy2, center=tuple(eye_ave), radius=1
        ##                   , color=(255, 255, 255),thickness = 2, lineType=cv2.LINE_AA)
        ##
        ##        out = np.bitwise_or(copy2, edge[:,:,np.newaxis])

        # cv2.imshow("Face", copy2)
        return cv2.cvtColor(copy2, cv2.COLOR_BGR2RGB)

    # 위의 함수를 이용하여 얼굴 점을 분석해 주는 것 ex 좋음 나쁨
    def FaceAnalyze(self):
        return
