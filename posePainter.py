from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QLabel
import math

pi = math.pi

baseColor = QColor()
baseColor.setNamedColor("#232d40")
snowColor = QColor()
snowColor.setNamedColor("#e1effa")
grayColor = QColor()
grayColor.setNamedColor("#558c8c8c")

greenColor = QColor()
greenColor.setNamedColor("#99ff33")
yellowColor = QColor()
yellowColor.setNamedColor("#ffff33")
orangeColor = QColor()
orangeColor.setNamedColor("#ff9933")
redColor = QColor()
redColor.setNamedColor("#ff3333")

score = 100


def getColor():
    global score

    if score <= 33:
        per = score * 3 / 100
        red = int(per * orangeColor.red() + (1 - per) * redColor.red())
        green = int(per * orangeColor.green() + (1 - per) * redColor.green())
        blue = int(per * orangeColor.blue() + (1 - per) * redColor.blue())
    elif score <= 66:
        per = (score - 33) * 3 / 100
        red = int(per * yellowColor.red() + (1 - per) * orangeColor.red())
        green = int(per * yellowColor.green() + (1 - per) * orangeColor.green())
        blue = int(per * yellowColor.blue() + (1 - per) * orangeColor.blue())
    else:
        per = (score - 66) * 3 / 100
        red = int(per * snowColor.red() + (1 - per) * yellowColor.red())
        green = int(per * snowColor.green() + (1 - per) * yellowColor.green())
        blue = int(per * snowColor.blue() + (1 - per) * yellowColor.blue())

    return QColor().fromRgb(red, green, blue)


def setScore(new_score):
    global score
    score = new_score


# 절레절레와 갸웃갸웃을 그려주는 클래스
class FrontPose(QLabel):
    global score

    def __init__(self, parent=None):
        super().__init__(parent)
        # 현 위젯의 가로/세로(w, h), 얼굴의 시작 좌표(x, y), 얼굴의 반지름(radius)
        self.w, self.h, self.x, self.y, self.radius = 0, 0, 0, 0, 0

        self.std_points = None

        self.std_eye = None
        self.std_nose = None
        self.std_mouse = None

        self.eye_points = None
        self.nose_points = None
        self.mouse_points = None

    # 크기가 바뀔 때 마다 값 크기에 맞게 설정한다.
    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.w = self.frameGeometry().width()
        self.h = self.frameGeometry().height()
        w = self.w
        h = self.h

        self.radius = h // 3
        self.x = (w // 2) - self.radius
        self.y = (h // 2) - self.radius

    # 기준 사진의 포인트들을 저장한다.
    def saveStandardShape(self, points):
        self.std_points = points

    # 기준 사진의 눈, 코, 입 좌표를 뷰에서 볼 수 있도록 정규화 한다.
    def setStandardShape(self):
        points = self.std_points

        f_x, f_y = points[0][0], points[0][1]
        leng = points[0][2]

        self.std_eye = self.standardization(f_x, f_y, leng, points[1])
        self.std_nose = self.standardization(f_x, f_y, leng, points[2])
        self.std_mouse = self.standardization(f_x, f_y, leng, points[3])

    # 프레임에 있던 눈, 코, 입 좌표를 뷰에서 볼 수 있도록 정규화를 한다.
    def setShape(self, points):
        f_x, f_y = points[0][0], points[0][1]
        leng = points[0][2]

        self.eye_points = self.standardization(f_x, f_y, leng, points[1])
        self.nose_points = self.standardization(f_x, f_y, leng, points[2])
        self.mouse_points = self.standardization(f_x, f_y, leng, points[3])

    # 리스트 내의 포인트들을 정규화 시키는 함수
    def standardization(self, f_x, f_y, leng, points):
        radius = self.radius
        x = self.x
        y = self.y

        temp = [[0, 0] for _ in range(len(points))]

        for num, [p_x, p_y] in enumerate(points):
            temp[num][0] = int((p_x - f_x) * ((radius * 2) / leng) + x)
            temp[num][1] = int((p_y - f_y) * ((radius * 2) / leng) + y + radius / 5)

        return temp

    # 기준 사진을 연하게 그려주는 함수
    def drawBase(self, qp):
        # 얼굴 경계선
        qp.drawEllipse(self.x, self.y, self.radius * 2, self.radius * 2)  # (x, y, w, h)
        # 눈
        points = self.std_eye
        for point in points:
            qp.drawEllipse(QPoint(point[0], point[1]), 2, 2)  # (center:QPoint, rx, ry)
        # 코
        points = self.std_nose
        for num in range(1, len(points)):
            qp.drawLine(points[num - 1][0], points[num - 1][1],
                        points[num][0], points[num][1])
        # 입
        points = self.std_mouse
        mid_x = int((points[0][0] + points[1][0]) / 2 + (points[0][1] - points[1][1]) / 2)
        mid_y = int((points[0][1] + points[1][1]) / 2 - (points[0][0] - points[1][0]) / 2)
        # 웃는 입 모양 그리기
        path = QPainterPath()
        path.moveTo(QPoint(points[0][0], points[0][1]))
        path.cubicTo(QPoint(points[0][0], points[0][1]),
                     QPoint(mid_x, mid_y),
                     QPoint(points[1][0], points[1][1]))
        qp.drawPath(path)

    def drawFrontPose(self, qp):
        # 얼굴 경계선
        qp.drawEllipse(self.x, self.y, self.radius * 2, self.radius * 2)  # (x, y, w, h)
        # 눈
        for point in self.eye_points:
            qp.drawEllipse(QPoint(point[0], point[1]), 2, 2)  # (center:QPoint, rx, ry)
        # 코
        points = self.nose_points
        for num in range(1, len(points)):
            qp.drawLine(points[num - 1][0], points[num - 1][1],
                        points[num][0], points[num][1])
        # 입
        points = self.mouse_points
        mid_x = int((points[0][0] + points[1][0]) / 2
                    - (points[1][1] - points[0][1]) * (score - 50) // 100)
        mid_y = int((points[0][1] + points[1][1]) / 2
                    + (points[1][0] - points[0][0]) * (score - 50) // 100)
        # 웃는 입 모양 그리기
        path = QPainterPath()
        path.moveTo(QPoint(points[0][0], points[0][1]))
        path.cubicTo(QPoint(points[0][0], points[0][1]),
                     QPoint(mid_x, mid_y),
                     QPoint(points[1][0], points[1][1]))
        qp.drawPath(path)

    def paintEvent(self, event):
        super().paintEvent(event)

        qp = QPainter(self)

        if self.eye_points is None:  # 창이 만들어진 직후 한번만 불린다.
            qp.setPen(QPen(snowColor, 4, Qt.SolidLine))
            self.setStandardShape()
            self.drawBase(qp)
        else:
            qp.setPen(QPen(grayColor, 4, Qt.SolidLine))
            self.drawBase(qp)

            qp.setPen(QPen(getColor(), 4, Qt.SolidLine))
            self.drawFrontPose(qp)

    # 클래스 내의 변수 값을 지워준다.
    def clear(self):
        self.eye_points = None
        self.nose_points = None
        self.mouse_points = None


# 거북목과 끄덕끄덕을 그려주는 클래스
class SidePose(QLabel):
    global score

    def __init__(self, parent=None):
        super().__init__(parent)

        self.w, self.h = 0, 0  # 현 위젯의 가로/세로(w, h)
        self.radius = 0  # 얼굴 반지름
        self.root_x, self.root_y, self.leng = 0, 0, 0  # 허리 시작점과 길이

        self.face_deg = None
        self.spine_deg = None

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.w = self.frameGeometry().width()
        self.h = self.frameGeometry().height()
        w = self.w
        h = self.h

        self.radius = h // 15 * 2

        self.leng = h // 15 * 6
        self.root_x = w // 2
        self.root_y = h // 6 * 5

    # 프레임에 기반한 허리와 얼굴의 각도 저장
    def setDegree(self, face_deg, spine_deg):
        self.spine_deg = int(spine_deg / 100 * 45)
        self.face_deg = face_deg

    # 옆모습을 그려주는 함수
    def drawSidePose(self, qp, spine_deg=0, face_deg=0):
        root_x, root_y, leng = self.root_x, self.root_y, self.leng
        radius = self.radius

        # 허리
        end_x = int(root_x + math.cos(math.radians(spine_deg - 90)) * leng)
        end_y = int(root_y + math.sin(math.radians(spine_deg - 90)) * leng)
        mid_x = int((root_x * 2 + end_x * 3) / 5 + (end_y - root_y) * spine_deg / 110)
        mid_y = int((root_y * 2 + end_y * 3) / 5 - (end_x - root_x) * spine_deg / 110)

        path = QPainterPath()
        path.moveTo(QPoint(root_x, root_y))
        path.cubicTo(QPoint(root_x, root_y),
                     QPoint(mid_x, mid_y),
                     QPoint(end_x, end_y))
        qp.drawPath(path)

        face_x = int(root_x + math.cos(math.radians(spine_deg - 90)) * (leng + radius))
        face_y = int(root_y + math.sin(math.radians(spine_deg - 90)) * (leng + radius))

        # 얼굴 (QPoint:center, rx, ry)
        qp.drawEllipse(QPoint(face_x, face_y), radius, radius)
        # 눈
        eye_x = int(face_x + math.cos(-pi / 4 - math.radians(face_deg)) * radius // 2)
        eye_y = int(face_y + math.sin(-pi / 4 - math.radians(face_deg)) * radius // 2)
        qp.drawEllipse(QPoint(eye_x, eye_y), 2, 2)  # (center:QPoint, rx, ry)
        # 코
        nose_x = int(face_x + math.cos(-pi / 18 - math.radians(face_deg)) * radius + 2)
        nose_y = int(face_y + math.sin(-pi / 18 - math.radians(face_deg)) * radius + 2)
        qp.drawEllipse(QPoint(nose_x, nose_y), 2, 2)  # (center:QPoint, rx, ry)
        # 입
        start_x = int(face_x + math.cos(pi / 3 - math.radians(face_deg)) * radius / 2 - 4)
        start_y = int(face_y + math.sin(pi / 3 - math.radians(face_deg)) * radius / 2 - 4)
        end_x = int(face_x + math.cos(pi / 4 - math.radians(face_deg)) * radius + 1)
        end_y = int(face_y + math.sin(pi / 4 - math.radians(face_deg)) * radius + 1)
        mid_x = int((start_x + end_x) / 2 - (end_y - start_y) * (score - 50) // 100)
        mid_y = int((start_y + end_y) / 2 + (end_x - start_x) * (score - 50) // 100)
        # 웃는 입 모양 그리기
        path = QPainterPath()
        path.moveTo(QPoint(start_x, start_y))
        path.cubicTo(QPoint(start_x, start_y),
                     QPoint(mid_x, mid_y),
                     QPoint(end_x, end_y))
        qp.drawPath(path)

    def paintEvent(self, event):
        super().paintEvent(event)

        qp = QPainter(self)

        if self.face_deg is None:  # 창이 만들어진 직후 한번만 불린다.
            qp.setPen(QPen(snowColor, 4, Qt.SolidLine))
            self.drawSidePose(qp)
        else:
            qp.setPen(QPen(grayColor, 4, Qt.SolidLine))
            self.drawSidePose(qp)

            color = getColor()
            qp.setPen(QPen(color, 4, Qt.SolidLine))
            self.drawSidePose(qp, self.spine_deg, self.face_deg)


# 자세 평가를 보이는 클래스
class PoseRater(QLabel):
    global score

    def __init__(self, parent=None):
        super().__init__(parent)

        # 현 위젯의 가로/세로(w, h), 의 시작 좌표(x, y), 얼굴의 반지름(radius)
        self.w, self.h, self.x, self.y, self.radius = 0, 0, 0, 0, 0
        self.deg_list = [-30, 30, 90, 150, 210]

    # 크기가 바뀔 때 마다 값 크기에 맞게 설정한다.
    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.w = self.frameGeometry().width()
        self.h = self.frameGeometry().height()
        w = self.w
        h = self.h

        self.radius = h // 3
        self.x = (w // 2) - self.radius
        self.y = (h // 2) - self.radius

    def paintEvent(self, event):
        super().paintEvent(event)

        x = self.x
        y = self.y
        radius = self.radius
        deg_list = self.deg_list

        qp = QPainter(self)

        # 바깥 둘레
        qp.setPen(QPen(greenColor, 4, Qt.SolidLine))
        qp.drawArc(x, y, radius * 2, radius * 2,
                   deg_list[0] * 16, (deg_list[1] - deg_list[0]) * 16)
        qp.setPen(QPen(yellowColor, 4, Qt.SolidLine))
        qp.drawArc(x, y, radius * 2, radius * 2,
                   deg_list[1] * 16, (deg_list[2] - deg_list[1]) * 16)
        qp.setPen(QPen(orangeColor, 4, Qt.SolidLine))
        qp.drawArc(x, y, radius * 2, radius * 2,
                   deg_list[2] * 16, (deg_list[3] - deg_list[2]) * 16)
        qp.setPen(QPen(redColor, 4, Qt.SolidLine))
        qp.drawArc(x, y, radius * 2, radius * 2,
                   deg_list[3] * 16, (deg_list[4] - deg_list[3]) * 16)

        # 안쪽 둘레
        inner = 12
        deg = int(-score / 100 * (deg_list[len(deg_list) - 1] - deg_list[0]))
        qp.setPen(QPen(grayColor, 8, Qt.SolidLine))
        qp.drawArc(x + inner, y + inner,
                   (radius - inner) * 2, (radius - inner) * 2,
                   deg_list[len(deg_list) - 1] * 16, deg * 16)

        # 수치
        # qp.
