from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor, QResizeEvent
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QLabel

snow = QColor()
snow.setNamedColor("#e1effa")
gray = QColor()
gray.setNamedColor("#558c8c8c")


# 절레절레와 갸웃갸웃을 그려주는 클래스
class FrontPose(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 현 위젯의 가로/세로(w, h), 얼굴의 시작 좌표(x, y), 얼굴의 반지름(radius)
        self.w, self.h, self.x, self.y, self.radius = 0, 0, 0, 0, 0

        # TODO 기존 위치 회색으로 보이기
        self.std_points = None
        self.need_stand = True

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
    def setStandardPoint(self, points):
        self.std_points = points

    # 기준 사진의 눈, 코, 입 좌표를 뷰에서 볼 수 있도록 정규화 한다.
    def setStandardShape(self):
        points = self.std_points

        f_x, f_y = points[0][0], points[0][1]
        leng = points[0][2]

        self.need_stand = True

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
        # 눈
        for point in self.std_eye:
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

    def paintEvent(self, event):
        super().paintEvent(event)

        radius = self.radius
        x = self.x
        y = self.y

        qp = QPainter(self)
        qp.setPen(QPen(snow, 4, Qt.SolidLine))

        # 얼굴 경계선
        qp.drawEllipse(x, y, radius * 2, radius * 2)  # (x, y, w, h)

        if self.eye_points is None:  # 창이 만들어진 직후 한번만 불린다.
            self.setStandardShape()
            self.drawBase(qp)
        else:
            qp.setPen(QPen(gray, 4, Qt.SolidLine))
            self.drawBase(qp)

            qp.setPen(QPen(snow, 4, Qt.SolidLine))

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
            mid_x = int((points[0][0] + points[1][0]) / 2 + (points[0][1] - points[1][1]) / 2)
            mid_y = int((points[0][1] + points[1][1]) / 2 - (points[0][0] - points[1][0]) / 2)
            # 웃는 입 모양 그리기
            path = QPainterPath()
            path.moveTo(QPoint(points[0][0], points[0][1]))
            path.cubicTo(QPoint(points[0][0], points[0][1]),
                         QPoint(mid_x, mid_y),
                         QPoint(points[1][0], points[1][1]))
            qp.drawPath(path)

            self.update()

    # 클래스 내의 변수 값을 지워준다.
    def clear(self):
        self.eye_points = None
        self.nose_points = None
        self.mouse_points = None


# 거북목과 끄덕끄덕을 그려주는 클래스
class SidePose(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.w, self.h = 0, 0   # 현 위젯의 가로/세로(w, h)
        self.radius = 0         # 얼굴 반지름
        self.x, self.y, self.leng = 0, 0, 0    # 허리 시작점과 길이

        self.face_deg = None
        self.spine_deg = None

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.w = self.frameGeometry().width()
        self.h = self.frameGeometry().height()
        w = self.w
        h = self.h

        self.radius = h * 2 // 15
        
        self.leng = h * 6 // 15
        self.x = w // 2
        self.y = h * 5 // 6

    # 기준 자세를 그려주는 함수
    def drawBase(self, qp):
        w, h = self.w, self.h
        x, y = self.x, self.y
        radius = self.radius

        # 얼굴 (QPoint:center, rx, ry)
        qp.drawEllipse(QPoint(w // 2, h * 3 // 10), radius, radius)
        # 허리
        qp.drawLine(x, y, x, h * 6 // 15)

    def paintEvent(self, event):
        super().paintEvent(event)

        qp = QPainter(self)

        if self.face_deg is None:  # 창이 만들어진 직후 한번만 불린다.
            qp.setPen(QPen(snow, 4, Qt.SolidLine))
            self.drawBase(qp)
        else:
            qp.setPen(QPen(gray, 4, Qt.SolidLine))
            self.drawBase(qp)

            self.update()

