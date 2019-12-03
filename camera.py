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

        self.std_pose = []  # 기준 자세 리스트
        self.cur_pose = []  # 현재 자세 리스트

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('!!')
        self.cam.release()
        # cv2.destroyAllWindows()

    # 이미지 존재여부와 이미지 자체와 이미지의 특징점을 반환하는 함수
    def faceDetect(self):
        ret, frame = self.cam.read()
        #좌우반전.
        frame = cv2.flip(frame, 1)
        frame = imutils.resize(frame, width=800)

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
                cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)

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

    # 기준 좌표 저장 (view의 MainView클래스의 confirmMassage함수에서 사용)
    def setStandardPose(self):
        self.std_pose = self.getPose(self.std_shape)
        return

    def getFrontShape(self):
        shape = self.std_shape
        face_info = self.getFaceInfo(shape)
        eye_points = [self.std_pose[4], self.std_pose[5]]
        nose_points = [shape[27], shape[30], shape[33]]
        mouse_points = [shape[48], shape[54]]
        # face info, [right eye, left eye], nose points, mouse points
        points = [face_info, eye_points, nose_points, mouse_points]

        return points

    def getSideShape(self):
        shape = self.std_shape

    # 0-mouth (0,1), 1-inner_mouth(2,3), 2-right_eyebrow(4,5), 3-left_eyebrow(6,7)
    # 4-right_eye(8,9), 5-left_eye(10,11), 6-nose(12,13), 7-jaw(14,15)
    # 특징점을 가지고 x축을 기준으로 몇도가 기울인지 반환 (끄덕끄덕)
    def visual_x_alarm(self):
        std_pose = self.std_pose
        cur_pose = self.cur_pose

        std_eye_y = (std_pose[2][1] + std_pose[3][1]) / 2
        cur_eye_y = (cur_pose[2][1] + cur_pose[3][1]) / 2

        #stability 계산을 위한 높이 변화 비율. 대략 40%가 최대치. 4/10.
        height_dif_per = abs((std_eye_y - cur_eye_y)/std_eye_y)
        
        #stability 값이 음수로 가는 것을 방지하기 위해 최대값 지정.
        if height_dif_per > 0.4:
            height_dif_per = 0.4
        
        # 10%정도 정상범위 제공.
        if std_eye_y * 1.05 < cur_eye_y:
            return "head UP plz", height_dif_per
        elif std_eye_y * 0.9 > cur_eye_y:
            return "head DOWN plz", height_dif_per
        else:
            return "x OK", height_dif_per

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
            math.asin((x1 * y2 - y1 * x2) / (math.sqrt(x1 * x1 + y1 * y1) * math.sqrt(x2 * x2 + y2 * y2)))
            * (180 / pi), 2)
        return y_angle

    # 특징점을 가지고 z축을 기준으로 몇도가 기울인지 반환 (절래절래)
    def visual_z_alarm(self):
        std_pose = self.std_pose
        cur_pose = self.cur_pose

        std_eye_w = std_pose[5][0] - std_pose[4][0]
        cur_eye_w = cur_pose[5][0] - cur_pose[4][0]
        temp = cur_eye_w / std_eye_w
        if temp >= 1.0:
            temp = 0.999999

        z_angle = math.acos(temp) * (180 / pi)
        return z_angle

    # 거북목. 상의 크기와 물체의 거리는 반비례.
    def visual_turtle_alarm(self):
        std_pose = self.std_pose
        cur_pose = self.cur_pose

        std_eye_w = std_pose[5][0] - std_pose[4][0]
        cur_eye_w = cur_pose[5][0] - cur_pose[4][0]
        std_brow_nose_h = ((std_pose[2][1] + std_pose[3][1]) / 2) - std_pose[6][1]
        cur_brow_nose_h = ((cur_pose[2][1] + cur_pose[3][1]) / 2) - cur_pose[6][1]
        std_nose_mouth_h = std_pose[6][1] - std_pose[1][1]
        cur_nose_mouth_h = cur_pose[6][1] - cur_pose[1][1]
        

        if abs(std_eye_w) < abs(cur_eye_w) and abs(std_brow_nose_h) < abs(cur_brow_nose_h) and abs(
                std_nose_mouth_h) < abs(cur_nose_mouth_h):
            # and std_nose_mouth_h < cur_nose_mouth_h
            #보통 값이 0.3까지 올라간다. 극단적인 경우 1.0까지 감.
            length_dif_per = (abs((std_eye_w - cur_eye_w)/std_eye_w)/3) + (abs((std_brow_nose_h - cur_brow_nose_h)/std_brow_nose_h)/3) + (abs((std_nose_mouth_h - cur_nose_mouth_h)/std_nose_mouth_h)/3)
                    #stability 값이 음수로 가는 것을 방지하기 위해 최대값 지정.
            if length_dif_per > 0.5:
                length_dif_per = 0.5
                
            return True, length_dif_per
        return False, 0

    # 저장했던 기준 좌표와 현 자세에 따라서 메시지 반환
    def getValues(self):
        stability = 0
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

            temp, x_val = self.visual_x_alarm()
            y_val = self.visual_y_alarm()
            z_val = self.visual_z_alarm()
            turtle_val, turtle_per = self.visual_turtle_alarm()
            stability = self.getStability(x_val, y_val, z_val, turtle_per)

            # return [int(x_val), int(y_val), int(z_val), turtle_val]
            return [x_val, int(y_val), int(z_val), turtle_val, stability], points

#일단 수치가 없는 x, turtle는 일괄적으로 점수를 감소, y, z는 각에 따라 감소
#값 비율은 x, y, z, turtle 순서대로 30 30 30 40.
    def getStability(self, x_per, y_angle, z_angle, turtle_per):
        stability = 100
        
        if x_per != 0:
            stability -= x_per * 75
        
        #각도-점수 좌표계의 1차 방정식. (10, 0) (30, 30)
        #1.5x - 15 = y. y가 뺄 점수, x가 입력 각도.
        if abs(y_angle) > 10:
            stability -= (abs(y_angle) * 1.5) - 15
              
        if abs(z_angle) > 10:
            stability -= (abs(z_angle) * 1.5) - 15
            
        if turtle_per != 0:
            stability -= turtle_per * 100
            
        return int(stability)
    