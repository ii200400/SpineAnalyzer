# https://www.youtube.com/watch?v=tpWVyJqehG4&vl=ko 참고 (im)
import imutils
from imutils import face_utils
import cv2
import dlib
import math

pi = math.pi


class ImageAnalyzer:
    def __init__(self):
        self.cam = cv2.VideoCapture(0)  # 카메라 지정 웹캠이 안되면 아래의 파일을 임시로 사용하겠다.

        self.detector = dlib.get_frontal_face_detector()  # 얼굴인식 모델
        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")  # 얼굴 특징점 모델

        self.std_frame = None
        self.std_shape = None
        self.std_hor_len = 0
        self.std_x_rate = 0
        self.std_y_rate = 0

        self.std_pose = []  # 기준 자세 리스트
        self.cur_pose = []  # 현재 자세 리스트

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('!!')
        self.cam.release()
        # cv2.destroyAllWindows()

    # 이미지 존재여부와 이미지 자체와 이미지의 특징점을 반환하는 함수
    def faceDetect(self):
        ret, frame = self.cam.read()
        frame = imutils.resize(frame, width=800)
        frame = cv2.flip(frame, 1)

        # 카메라는 연결이 되어있는데 어떤 이유로 이미지를 불러오지 못하면 false가 나오기는 한다.
        if not ret:
            print('아이고..')
            return 0, (None, None)

        # 얼굴 인식
        faces = self.detector(frame)
        if len(faces) == 0:  # 인식되는 얼굴이 없는 경우
            # TODO 개발자용 코드
            cv2.imshow("Frame", frame)
            return 1, (frame, None)

        # 첫번째로 인식되는 얼굴만 탐색
        face = faces[0]

        # 얼굴 특징점 인식
        shape = self.predictor(frame, face)
        shape = face_utils.shape_to_np(shape)
        return 2, (frame, shape)

    # 이미지에 특징점을 그리는 함수
    def drawPoints(self, frame, shape):
        # TODO 개발자 용 코드(1줄)
        copy = frame.copy()

        # 특징점들의 그룹과 그룹의 범위
        for (name, (i, j)) in face_utils.FACIAL_LANDMARKS_IDXS.items():
            # TODO 개발자 용 코드(1줄)
            meanx, meany, count = 0, 0, 0

            # 얼굴 특징점에 점 그리기
            for (x, y) in shape[i:j]:
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

                # TODO 개발자 용 코드(8줄)
                cv2.circle(copy, (x, y), 1, (0, 0, 255), -1)

                meanx += x
                meany += y
                count += 1

            meanx = int(meanx / count)
            meany = int(meany / count)
            cv2.circle(copy, (meanx, meany), 3, (0, 255, 0), -1)

        cv2.imshow("Frame", copy)

        return frame

    # 특징점에서 그룹별로 평균 점을 구하고 저장하는 함수
    def getPose(self, shape):
        avePoints = [[0, 0] for _ in range(8)]

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

    def getFaceInfo(self, shape):
        left, right, top = 9999, 0, 9999

        for name, (i, j) in imutils.face_utils.FACIAL_LANDMARKS_IDXS.items():
            if name in ["right_eyebrow", "left_eyebrow", "jaw"]:
                for (x, y) in shape[i:j]:
                    if left > x: left = x
                    if right < x: right = x
                    if top > y: top = y

        return [left, top, right - left]

    # facedetect함수의 결과에 따라서 다른 이미지를 반환하는 함수 (view의 MainView클래스의 showImage함수에서 쓰인다.)
    def getFrame(self):
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

    # 기준 좌표 저장 (view의 MainView클래스의 confirmMassage함수에서 사용)
    def setStandardPose(self):
        std_shape = self.std_shape
        self.std_pose = self.getPose(std_shape)

        std_pose = self.std_pose
        x1 = std_shape[16][0] - std_shape[0][0]
        y1 = std_shape[16][1] - std_shape[0][1]
        x2 = std_pose[7][0] - std_pose[0][0]
        y2 = std_pose[7][1] - std_pose[0][1]

        self.std_hor_len = math.sqrt(x1 ** 2 + y1 ** 2)
        hor_len = self.std_hor_len
        ver_len = math.sqrt((std_shape[8][0] - std_shape[27][0]) ** 2 +
                            (std_shape[8][1] - std_shape[27][1]) ** 2)
        m_to_j = math.sqrt(x2 ** 2 + y2 ** 2)

        if m_to_j == 0:
            self.std_x_rate = 0
            self.std_y_rate = 0
        else:
            angle = round(
                math.asin((x1 * y2 - y1 * x2) / (hor_len * m_to_j))
                * (180 / pi), 2)

            rad = math.radians(angle)
            self.std_x_rate = round(math.cos(rad) * m_to_j / hor_len * 100)
            self.std_y_rate = round(math.sin(rad) * m_to_j / ver_len * 100)

            if x2 < 0:
                self.std_x_rate = -self.std_x_rate

    def getFrontShape(self):
        shape = self.std_shape
        face_info = self.getFaceInfo(shape)
        eye_points = [self.std_pose[4], self.std_pose[5]]
        nose_points = [shape[27], shape[30], shape[33]]
        mouse_points = [shape[48], shape[54]]
        # face info, [right eye, left eye], nose points, mouse points
        points = [face_info, eye_points, nose_points, mouse_points]

        return points

    # TODO face_deg 등 반환
    def getSideShape(self):
        shape = self.std_shape

    # 0-mouth (0,1), 1-inner_mouth(2,3), 2-right_eyebrow(4,5), 3-left_eyebrow(6,7)
    # 4-right_eye(8,9), 5-left_eye(10,11), 6-nose(12,13), 7-jaw(14,15)
    # 특징점을 가지고 x축을 기준으로 몇도가 기울인지 반환 (끄덕끄덕)
    def visual_xz_alarm(self, cur_shape):
        cur_pose = self.cur_pose

        x1 = cur_shape[16][0] - cur_shape[0][0]
        y1 = cur_shape[16][1] - cur_shape[0][1]
        x2 = cur_pose[7][0] - cur_pose[0][0]
        y2 = cur_pose[7][1] - cur_pose[0][1]

        hor_len = math.sqrt(x1 ** 2 + y1 ** 2)
        ver_len = math.sqrt((cur_shape[8][0] - cur_shape[27][0]) ** 2 +
                            (cur_shape[8][1] - cur_shape[27][1]) ** 2)
        m_to_j = math.sqrt(x2 ** 2 + y2 ** 2)

        if m_to_j == 0:
            cur_x_rate = 0
            cur_y_rate = 0
        else:
            angle = round(
                math.asin((x1 * y2 - y1 * x2) / (hor_len * m_to_j))
                * (180 / pi), 2)

            rad = math.radians(angle)
            cur_x_rate = int(math.cos(rad) * m_to_j / hor_len * 100)
            cur_y_rate = int(math.sin(rad) * m_to_j / ver_len * 100)

            if x2 < 0:
                cur_x_rate = -cur_x_rate

        # 1.5배를 하면 각도와 얼추 비슷하게 나와서 곱함
        x_angle = (cur_x_rate - self.std_x_rate) * 1.5
        z_angle = (cur_y_rate - self.std_y_rate) * 1.5  # 이름 잘못 쓴거 아니다!!

        return x_angle, z_angle

    # 특징점을 가지고 y축을 기준으로 몇도가 기울인지 반환 (갸웃갸웃)
    def visual_y_alarm(self):
        std_pose = self.std_pose
        cur_pose = self.cur_pose

        x1 = std_pose[4][0] - std_pose[5][0]
        y1 = std_pose[4][1] - std_pose[5][1]
        x2 = cur_pose[4][0] - cur_pose[5][0]
        y2 = cur_pose[4][1] - cur_pose[5][1]
        # 우측 값이 라디안이라 180/np.pi 로 360도 값으로 변환.
        y_angle = round(
            math.asin((x1 * y2 - y1 * x2) / (math.sqrt(x1 ** 2 + y1 ** 2) * math.sqrt(x2 ** 2 + y2 ** 2)))
            * (180 / pi), 2)

        return y_angle

    # 거북목. 상의 크기와 물체의 거리는 반비례.
    def visual_turtle_alarm(self, cur_shape):
        std_shape = self.std_shape
        w = len(self.std_frame[0])

        std_hor_len = self.std_hor_len
        cur_hor_len = math.sqrt((cur_shape[16][0] - cur_shape[0][0]) ** 2
                                + (cur_shape[16][1] - cur_shape[0][1]) ** 2)
        # 예를 들면 1/3이 아니라 3이 계산에 필요하다.
        std_dis = w / std_hor_len
        cur_dis = w / cur_hor_len

        rate = (std_dis - cur_dis) / 1.5 * 100
        if rate > 100:
            rate = 100

        return int(rate)

    # 저장했던 기준 좌표와 현 자세에 따라서 메시지 반환
    def getValues(self):
        status, (frame, shape) = self.faceDetect()

        if status in [0, 1]:
            return None, None

        elif status == 2:
            # TODO 개발자용 코드(1줄 / 개별 창으로 실재 상태를 보이기 위해서 사용)
            self.drawPoints(frame, shape)

            self.cur_pose = self.getPose(shape)

            face_info = self.getFaceInfo(shape)
            eye_points = [self.cur_pose[4], self.cur_pose[5]]
            nose_points = [shape[27], shape[30], shape[33]]
            mouse_points = [shape[48], shape[54]]
            # face info, [right eye, left eye], nose points, mouse points
            points = [face_info, eye_points, nose_points, mouse_points]

            x_angle, z_angle = self.visual_xz_alarm(shape)
            y_angel = self.visual_y_alarm()
            turtle_per = self.visual_turtle_alarm(shape)
            score = self.getStability(x_angle, y_angel, z_angle, turtle_per)
            print(x_angle, y_angel, z_angle, turtle_per, score)

            # 각도, 각도, 각도, 퍼센티지, 포인트들, 점수
            # return [x_val, y_val, z_val, turtle_val], points, score

    def getStability(self, x_angle, y_angle, z_angle, turtle_per):
        stability = 100

        if x_angle != 0:
            stability -= x_angle * 75

        # 각도-점수 좌표계의 1차 방정식. (10, 0) (30, 30)
        # 1.5x - 15 = y. y가 뺄 점수, x가 입력 각도.
        if abs(y_angle) > 10:
            stability -= (abs(y_angle) * 1.5) - 15

        if abs(z_angle) > 10:
            stability -= (abs(z_angle) * 1.5) - 15

        if turtle_per != 0:
            stability -= turtle_per * 100

        return int(stability)
