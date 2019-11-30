from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor, QResizeEvent
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QLabel

snow = QColor()
snow.setNamedColor("#e1effa")


class FrontPose(QLabel):
    x, y, w, h, radius = 0, 0, 0, 0, 0

    def __init__(self, parent=None):
        super().__init__(parent)

        self.eye_points = None
        self.nose_points = None
        self.mouse_points = None

    def resizeEvent(self, a0: QResizeEvent) -> None:
        global x, y, w, h, radius

        w = self.frameGeometry().width()
        h = self.frameGeometry().height()

        radius = h // 3
        x = (w // 2) - radius
        y = (h // 2) - radius

    # 프레임에 있던 눈, 코, 입 좌표를 뷰에서 볼 수 있도록 정규화를 한다.
    def setShape(self, points):
        f_x, f_y = points[0][0], points[0][1]
        leng = points[0][2]

        self.eye_points = self.standardization(f_x, f_y, leng, points[1])
        self.nose_points = self.standardization(f_x, f_y, leng, points[2])
        self.mouse_points = self.standardization(f_x, f_y, leng, points[3])

    def standardization(self, f_x, f_y, leng, points):
        temp = [[0, 0] for _ in range(len(points))]

        for num, [p_x, p_y] in enumerate(points):
            temp[num][0] = int((p_x - f_x) * ((radius * 2) / leng) + x)
            temp[num][1] = int((p_y - f_y) * ((radius * 2) / leng) + y + radius // 5)

        return temp

    def paintEvent(self, event):
        super().paintEvent(event)

        # 동그라미를 그릴 때 사용하는 가장 왼쪽 위의 좌표와 원의 반지름
        qp = QPainter(self)
        qp.setPen(QPen(snow, 4, Qt.SolidLine))

        # 얼굴 경계선
        qp.drawEllipse(x, y, radius * 2, radius * 2)  # (x, y, w, h)

        if self.eye_points is not None:
            # 눈
            for point in self.eye_points:
                qp.drawEllipse(QPoint(point[0], point[1]), 2, 2)    #(center:QPoint, rx, ry)
            # 코
            points = self.nose_points
            for num in range(1, len(points)):
                qp.drawLine(points[num-1][0], points[num-1][1],
                            points[num][0], points[num][1])
            # 입
            points = self.mouse_points
            mid_x = int((points[0][0] + points[1][0]) / 2 + (points[0][1] - points[1][1]) / 4)
            mid_y = int((points[0][1] + points[1][1]) / 2 - (points[0][0] - points[1][0]) / 4)
            # 웃는 입 모양 그리기
            path = QPainterPath()
            path.moveTo(QPoint(points[0][0], points[0][1]))
            path.cubicTo(QPoint(points[0][0], points[0][1]),
                         QPoint(mid_x, mid_y),
                         QPoint(points[1][0], points[1][1]))
            qp.drawPath(path)

            self.update()
