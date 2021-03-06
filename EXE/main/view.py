# 쓸만한 색 모음
# RGB
# 36 /220/148 기본 컬러 #24dc94
# 35 /45 / 64 * 더 진파색 #232d40
# 25 /58 /100 * 진파색 #193a64
# 36 /46 /95
# 81 /136/195
# 116/168/219 * 연파색 #74a8db
# 2  /174/240
# 11 /203/229
# 225/239/250 * 눈색 #e1effa
# 60 /63 /65  * 고동색 #3c3f41
# 204/204/204  * 회색 #cccccc

# TODO 글꼴 확인, 문구 추가

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pygame import mixer
import random

import camera
import posePainter
import fairyScript


class MainView(object):
    pass


class MoniterView(object):
    pass


cameraObject: camera.ImageAnalyzer  # 카메라 객체
mainView: MainView  # 메인화면 객체 (지역변수로 사용하니 함수가 종료되면서 사라져서 임시적 조치로 여기에 정의)
moniterView: MoniterView  # 탭 화면 객체

fps: int = 40  # FPS값
volume: int = 100  # 음향 크기
isOnlySound: bool = True


# 텍스트로 값을 바꿀 때 불리는 함수
def pressEnter(slider, text):
    textValue = text.text()

    # 음수 값에 대한 예외처리
    temp = textValue
    if temp[0] == '-':
        temp = temp[1:]

    # 넣은 값이 숫자인지 확인
    if not temp.isdecimal():
        text.setText(str(fps))
        return

    textValue = int(textValue)
    minValue = slider.minimum()
    maxValue = slider.maximum()

    # 아래의 코드로도 슬라이더 값을 바꾸는 것이기 때문에
    # 자동으로 setSlider 함수가 불린다.
    if textValue < minValue:  # 슬라이더의 최소값보다 작은 경우
        slider.setValue(minValue)
        text.setText(str(minValue))
    elif textValue > maxValue:  # 슬라이더의 최대값보다 큰 경우
        slider.setValue(maxValue)
        text.setText(str(maxValue))
    else:  # 적정한 값의 경우
        slider.setValue(textValue)


# 슬라이더로 fps를 바꿀 때 불리는 함수
def setSliderFPS(slider, text, timer):
    global fps

    fps = slider.value()
    text.setText(str(fps))

    timer.start(1000 // fps)


# 슬라이더로 음향 크기를 바꿀 때 불리는 함수
def setSliderVolume(slider, text):
    global volume

    volume = slider.value()
    text.setText(str(volume))


# moniterView 초기화
def mainShowSetting():
    moniterView.analyzeTap.timer.stop()
    moniterView.analyzeTap.alarm_timer.stop()
    moniterView.analyzeTap.w_alarm_timer.stop()

    moniterView.analyzeTap.status_front.clear()
    moniterView.analyzeTap.status_side.clear()

    moniterView.analyzeTap.status_front.repaint()
    moniterView.analyzeTap.status_side.repaint()
    moniterView.analyzeTap.status_rater.repaint()


def mainHideSetting():
    moniterView.analyzeTap.status_front.saveStandardShape(cameraObject.getFrontShape())
    posePainter.setScore(100)
    posePainter.setLine(Qt.SolidLine)

    moniterView.analyzeTap.timer.start(1000 // fps)
    moniterView.analyzeTap.alarm_timer.start(5000)
    moniterView.analyzeTap.w_alarm_timer.start(5000)


# 로딩 화면
class SplashView(QWidget):

    def __init__(self):
        super().__init__()

        self.logo_label = QLabel()  # 로고
        self.logo_text = QLabel('Posture Fairy')  # 로고 텍스트

        self.timer = QTimer()  # 타이머 (로딩 화면에 머무르는 최소 기간)

        self.initUI()

    def initUI(self):
        # 로고와 로고 텍스트, 타이머 설정
        self.logo_label.setPixmap(
            QPixmap('./image/fairy-256.png').scaled(
                192,
                192,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setMargin(32)

        self.logo_text.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.logo_text.setStyleSheet("color: #e1effa")
        self.logo_text.setFont(QFont("나눔바른펜", 30, 100))

        self.timer.timeout.connect(self.startInit)
        self.timer.start(500)  # 단위 : 마이크로세컨드

        # 레이아웃 설정
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.logo_label)
        vbox1.addWidget(self.logo_text)

        self.setLayout(vbox1)

        # 창 설정
        self.activateWindow()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #232d40")
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(screen.width() // 2 - 400, screen.height() // 2 - 200, 800, 400)
        self.setFixedSize(800, 400)

    # 로딩이 끝나면 알아서 이 창을 닫고 메인 화면으로 전환이 되도록 한다.
    def startInit(self):
        global mainView

        self.timer.stop()
        mainView = MainView()
        mainView.timer.start(1000 // fps)  # 단위 : 마이크로세컨드
        mainView.show()

        self.close()


# 메인 화면
class MainView(QWidget):

    def __init__(self):
        global moniterView

        super().__init__()

        moniterView = MoniterView()

        self.camera_label = QLabel()  # 카메라로 찍는 영상이 보이는 라벨
        self.camera_but = QPushButton()  # 카메라 영상의 갱신을 멈추는 버튼

        # FPS에 관한 위젯들
        self.fps_text = QLabel("프레임")
        self.slider = QSlider(Qt.Vertical, self)
        self.slider_text = QLineEdit(str(fps))

        self.timer = QTimer()  # 카메라 영상을 갱신할 때 사용하는 타이머

        self.isface = False  # 카메라에 얼굴이 탐색 되었는지

        self.initUI()

    def initUI(self):
        global cameraObject

        cameraObject = camera.ImageAnalyzer()  # 카메라 객체 생성

        # 카메라 버튼에 관한 설정
        self.camera_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.camera_but.setFixedSize(72, 72)
        self.camera_but.setIcon(QIcon('./image/camera.png'))
        self.camera_but.setIconSize(QSize(36, 36))
        self.camera_but.released.connect(self.confirmMassage)
        self.camera_but.setStyleSheet("QPushButton  {border: 2px solid #cccccc; border-radius: 36px;"
                                      "background-color: #cccccc; }"
                                      "QPushButton:pressed { background-color: #8c8c8c; }")

        # FPS 라벨, 슬라이더, 텍스트 상세 설정
        self.fps_text.setFont(QFont('나눔바른펜', 12, 100))
        self.fps_text.setStyleSheet("color: #232d40; margin: 10px 0px 0px 0px;")
        self.fps_text.setAlignment(Qt.AlignCenter)
        self.fps_text.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.slider.setRange(20, 80)
        self.slider.setTickPosition(QSlider.TicksRight)
        self.slider.setTickInterval(5)
        self.slider.setSliderPosition(fps)
        # self.slider.setFixedHeight(self.height() * 6 // 10)
        self.slider.valueChanged.connect(lambda x: setSliderFPS(self.slider, self.slider_text, self.timer))
        self.slider.setStyleSheet("QSlider { padding: 10px 10px; }"
                                  "QSlider::groove:vertical {"
                                  "background: #cccccc; position: absolute; left: 11px; right: 11px; }"
                                  "QSlider::handle:vertical { "
                                  "height: 8px; background: white; margin: 0 -8px;"
                                  "border: 1px solid #232d40; border-radius: 4px; }"
                                  "QSlider::add-page:vertical { background: #99ddff; "
                                  "border: 0px solid ; border-radius: 1px; }")

        self.slider.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)

        self.slider_text.editingFinished.connect(lambda: pressEnter(self.slider, self.slider_text))
        self.slider_text.setStyleSheet("background-color: #cccccc; color: #e1effa"
                                       "margin: 10px 2px")

        # 카메라 타이머 설정
        self.timer.timeout.connect(self.showImage)
        self.timer.stop()

        # 텍스트들을 모아놓을 그룹 세부 설정
        guideBox = QGroupBox('사용 방법')
        guideBox.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        # 아 드럽게 어렵네..
        guideBox.setStyleSheet("QGroupBox { "
                               "margin: 15px; margin-top: 20px; padding-top: 5px; "
                               "border: 2px solid #e1effa; border-radius: 5px; "
                               "font-family: '나눔바른펜'; font-size: 15pt; font-weight: bold; color: #e1effa; }"
                               "QGroupBox:title { "
                               "subcontrol-origin: margin; subcontrol-position: top center; "
                               "padding: 5px 5px 5px 5px; }")

        # 사용 설병을 명세한 텍스트
        guideText1 = QLabel('1. 노트북 카메라 혹은 웹캠을 사용가능한 상태로 설정해주세요.')
        guideText2 = QLabel('2. 얼굴이 인식되는 상태로 하단의 카메라 버튼을 눌러 정면 사진을 찍어주세요.')
        guideText3 = QLabel('3. 자신의 자세를 실시간으로 확인하세요.')
        guideText4 = QLabel('-TIP-')
        guideText5 = QLabel('1. 가장 이상적인 자세를 한 상태로 사진을 찍어주세요.')
        guideText6 = QLabel('2. 얼굴에 그림자가 지지 않도록 찍으세요.')
        guideText7 = QLabel('3. 얼굴이 중앙에 오도록 찍어주세요.')

        # 텍스트를 그룹에 배치
        t = QVBoxLayout()
        t.addWidget(guideText1)
        t.addWidget(guideText2)
        t.addWidget(guideText3)
        t.addWidget(guideText4)
        t.addWidget(guideText5)
        t.addWidget(guideText6)
        t.addWidget(guideText7)
        guideBox.setLayout(t)

        # 각 텍스트에 같은 스타일을 설정
        guidetexts = guideBox.findChildren(QLabel)
        for text in guidetexts:
            text.setFont(QFont('나눔바른펜', 12, 50))
            text.setStyleSheet("color: #e1effa")
            text.setWordWrap(True)

        guideText4.setAlignment(Qt.AlignCenter)
        guideText4.setFont(QFont('나눔바른펜', 12, 100))

        # 그룹에 배경 색상을 지정하지 못하는 문제로 
        # 위젯에 배경을 설정하고 그 위젯을 그룹에 넣는 것으로 해결..;
        container = QWidget()
        container.setStyleSheet("background-color: #e1effa")

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.camera_label)
        vbox2.addWidget(self.camera_but, 0, Qt.AlignHCenter)
        vbox2.setAlignment(Qt.AlignHCenter)

        # FPS에 관한 위젯 배치
        vbox3 = QVBoxLayout()
        vbox3.addWidget(self.fps_text, 1)
        vbox3.addWidget(self.slider, 8)
        vbox3.addWidget(self.slider_text, 1)

        # 카메라와 FPS에 관한 위젯들 배치 및 배경 색상 지정
        hbox_t = QHBoxLayout()
        hbox_t.addLayout(vbox2, 9)
        hbox_t.addLayout(vbox3, 1)

        container.setLayout(hbox_t)

        # 위의 것과 설명 텍스트 배치
        hbox = QHBoxLayout()
        hbox.addWidget(guideBox, 45)
        hbox.addWidget(container, 55)
        hbox.setContentsMargins(0, 0, 0, 0)

        self.setLayout(hbox)

        # 창 설정
        self.setStyleSheet("background-color: #232d40")
        self.setWindowTitle('Posture Fairy')
        self.setWindowIcon(QIcon('./image/fairy-32.png'))
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(screen.width() // 2 - 400, screen.height() // 2 - 200, 800, 400)
        self.setMinimumSize(800, 400)
        # self.setFixedSize(800, 400)

    # 창이 생겨나기전 값 초기화
    def showEvent(self, a0: QShowEvent) -> None:
        self.timer.start(1000 // fps)

        self.activateWindow()

    # 메시지 박스가 나오면서 동영상이 멈추고 확인 버튼을 누르면 다음 창이 뜬다.
    def confirmMassage(self):
        self.timer.stop()

        # 메세지 창 생성 및 세부 설정
        message = QMessageBox()
        message.setWindowIcon(QIcon('./image/fairy-32.png'))
        message.setStyleSheet("QMessageBox { background-color: #232d40;}"
                              "QMessageBox QLabel { "
                              "padding: 20px 5px 5px 5px;"
                              "font-family: '나눔바른펜'; font-size: 12pt; color: #e1effa; }"
                              "QMessageBox QPushButton { "
                              "background-color: #cccccc; margin: 5px; padding: 5px 15px 5px 15px; "
                              "font-family: '나눔고딕'; font-size: 10pt; font-weight: bold; color: #232d40"
                              "border: 2px solid #232d40; border-radius: 5px; }"
                              "QMessageBox QPushButton:pressed { background-color: #8c8c8c; }")

        if not self.isface:
            message.setWindowTitle("Warning")
            message.setText("얼굴이 인식되지 않았습니다.\n다시 찍어주세요.")
            message.setIcon(QMessageBox.Warning)
            message.setStandardButtons(QMessageBox.Yes)
            message.setDefaultButton(QMessageBox.Yes)

            message.exec_()

            self.timer.start(1000 // fps)

        else:
            message.setWindowTitle("확인")
            message.setText("이 사진으로 하시겠습니까?")
            message.setIcon(QMessageBox.Question)
            message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            message.setDefaultButton(QMessageBox.No)

            # 메세지 창 버튼에 대한 결과
            answer = message.exec_()

            if answer == QMessageBox.Yes:  # 확인 버튼을 눌렀다면 현재 창을 숨기고 다른 창을 보인다.
                cameraObject.setStandardPose()

                mainHideSetting()

                self.hide()
                moniterView.show()
            else:  # 취소 버튼을 눌렀다면 타이머를 다시 시작한다.
                self.timer.start(1000 // fps)

    # 카메라 객체에서 이미지를 받아와서 뷰 화면에서 보이도록 한다.
    def showImage(self):
        status, frame = cameraObject.getFrame()

        if status == 0:  # 이미지가 반환되지 않았을 때
            pix = QPixmap('./image/disconnected').scaled(
                128,
                128,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation)
            self.camera_label.setPixmap(pix)

        elif status in [1, 2]:  # 이미지가 성공적으로 반환되었을 때
            qImg = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pix = QPixmap.fromImage(qImg).scaled(
                self.camera_label.width(),
                self.camera_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation)

        if status == 2:
            self.isface = True
        else:
            self.isface = False

        self.camera_label.setPixmap(pix)
        return status


# 텝이 있는 창, 첫 탭은 현재 상태를 보이는 탭이고 두번째 탭은 설정을 바꿀 수 있는 창이다.
class MoniterView(QDialog):
    def __init__(self):
        super().__init__()

        self.tabs = QTabWidget()

        self.analyzeTap = AnalyzerTap()
        self.settingTap = SettingTap()

        self.setStyleSheet("QDialog { background-color: #232d40;}")
        self.initUI()

    def initUI(self):
        # 탭을 넣을 위젯 생성 및 세부 설정
        self.tabs.setMovable(True)
        self.tabs.setStyleSheet("QTabWidget::pane { background-color: #232d40;"
                                "border: 2px solid #e1effa; border-radius: 4px; border-top-left-radius: 0px; }"
                                "QTabBar::tab {"
                                # "background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.3 #232d40, stop: 1.0 #e1effa);"
                                "border: 2px solid #e1effa; border-bottom-color: #232d40;"
                                "background: #232d40;"
                                "font-family: '나눔고딕'; font-size: 8pt; font-weight: bold; color: #e1effa;"
                                "border-top-left-radius: 4px; border-top-right-radius: 4px;"
                                "min-width: 15ex; padding: 5px; }"
                                "QTabBar::tab:!selected:hover { background: #cccccc }"
                                "QTabBar::tab:!selected { "
                                "border-bottom-color: #e1effa; border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;"
                                "margin: 5px; padding: 3px; background: #e1effa; color: #232d40;}")

        # 탭 추가
        self.tabs.addTab(self.analyzeTap, '상태')
        self.tabs.addTab(self.settingTap, '설정')

        # 레이아웃 생성 및 설정
        hbox = QHBoxLayout()
        hbox.addWidget(self.tabs)

        self.setLayout(hbox)

        # 창 설정
        # Qt.WindowSystemMenuHint | WindowTitleHint | WindowCloseButtonHint
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Posture Fairy')
        self.setWindowIcon(QIcon('./image/fairy-32.png'))
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, screen.height() - 350, 600, 300)
        self.setFixedSize(600, 300)

    def showEvent(self, a0: QShowEvent) -> None:
        self.tabs.setCurrentIndex(0)


# 첫번째 탭
class AnalyzerTap(QWidget):

    def __init__(self):
        super().__init__()

        self.alarm_window = AlarmWindow()

        self.front_label = QLabel("앞 모습")
        self.side_label = QLabel("옆 모습")
        self.rater_label = QLabel("자세 평가")

        self.status_front = posePainter.FrontPose()  # 사용자 상태를 반영하는 애니메이션
        self.status_side = posePainter.SidePose()  # 사용자 상태를 반영하는 이미지
        self.status_rater = posePainter.PoseRater()

        self.audio = mixer
        self.save_time = 0
        self.save_w_time = 0

        self.timer = QTimer()
        self.alarm_timer = QTimer()
        self.w_alarm_timer = QTimer()
        self.see_timer = QTimer()

        self.initUI()

    def initUI(self):
        for label in [self.front_label, self.side_label, self.rater_label]:
            label.setStyleSheet("color: #e1effa")  # background-color: #8c8c8c
            label.setFont(QFont("나눔바른펜", 15, 100))
            label.setAlignment(Qt.AlignCenter)

        for status in [self.status_front, self.status_side, self.status_rater]:
            status.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
            status.setAlignment(Qt.AlignCenter)

        self.audio.init()

        self.alarm_timer.timeout.connect(self.soundAlarm)
        self.alarm_timer.stop()

        self.w_alarm_timer.timeout.connect(self.showAlarmWindow)
        self.w_alarm_timer.stop()

        self.timer.timeout.connect(self.analyzeImage)
        self.timer.stop()

        self.see_timer.timeout.connect(self.userGone)
        self.see_timer.stop()

        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.side_label)
        vbox1.addWidget(self.status_side)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.front_label)
        vbox2.addWidget(self.status_front)

        vbox3 = QVBoxLayout()
        vbox3.addWidget(self.rater_label)
        vbox3.addWidget(self.status_rater)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox1, 1)
        hbox.addLayout(vbox2, 1)
        hbox.addLayout(vbox3, 1)

        self.setLayout(hbox)

    # 자세를 분석한 결과를 메시지로 보여주는 함수
    def analyzeImage(self):
        values, points, score = cameraObject.getValues()

        # print(self.alarm_timer.remainingTime())
        if values is not None:
            if self.see_timer.isActive():
                remain = self.see_timer.remainingTime()

                # TODO 2초 이하는 잠깐씩 얼굴인식이 안 되었다고 생각한다.
                if remain > 28000:
                    self.alarm_timer.start(
                        max(1, self.save_time - (30000 - remain)))
                    self.w_alarm_timer.start(
                        max(1, self.save_w_time - (30000 - remain)))

                else:
                    self.alarm_timer.start(5000)
                    self.w_alarm_timer.start(5000)

                self.see_timer.stop()

            posePainter.setScore(score)
            posePainter.setLine(Qt.SolidLine)

            self.status_front.setShape(points)
            self.status_side.setDegree(values[0], values[3])

            if score > 80:
                self.alarm_timer.start(5000)
                self.w_alarm_timer.start(5000)

        else:
            if not self.see_timer.isActive():
                self.see_timer.start(30000)

                self.save_time = self.alarm_timer.remainingTime()
                self.save_w_time = self.w_alarm_timer.remainingTime()

                self.alarm_timer.stop()
                self.w_alarm_timer.stop()

            # TODO 2초가 지나면 점선으로 변하여 얼굴 인식이 되고있지 않음을 보여준다.
            elif self.see_timer.remainingTime() < 28000:
                posePainter.setLine(Qt.DotLine)

        self.status_front.repaint()
        self.status_side.repaint()
        self.status_rater.repaint()

        # print(self.alarm_timer.remainingTime())

    # 알림창이 나오도록 하는 함수
    def showAlarmWindow(self):
        if not isOnlySound:
            self.alarm_window.show()
            self.w_alarm_timer.stop()
        else:
            self.w_alarm_timer.start(5000)

    # 알람 소리가 나도록 하는 함수
    def soundAlarm(self):
        print("sound!!")

        if isOnlySound:
            self.audio.music.load("./sound/sayHuri.mp3")

            self.audio.music.set_volume(volume / 100)
            self.audio.music.play()

        self.alarm_timer.start(5000)

    def userGone(self):
        self.see_timer.stop()

        mainShowSetting()

        moniterView.hide()
        mainView.show()

        message = QMessageBox()
        message.setWindowIcon(QIcon('./image/fairy-32.png'))
        message.setWindowTitle("알림")
        message.setText("오랜 시간 얼굴을 인식하지 못하여 사진을 다시 찍어야 합니다.")
        message.setIcon(QMessageBox.Warning)
        message.setStandardButtons(QMessageBox.Yes)
        message.setDefaultButton(QMessageBox.Yes)
        message.setStyleSheet("QMessageBox { background-color: #232d40;}"
                              "QMessageBox QLabel { "
                              "padding: 20px 5px 5px 5px;"
                              "font-family: '나눔바른펜'; font-size: 12pt; color: #e1effa; }"
                              "QMessageBox QPushButton { "
                              "background-color: #cccccc; margin: 5px; padding: 5px 15px 5px 15px; "
                              "font-family: '나눔고딕'; font-size: 10pt; font-weight: bold; color: #232d40"
                              "border: 2px solid #232d40; border-radius: 5px; }"
                              "QMessageBox QPushButton:pressed { background-color: #8c8c8c; }")

        # 메세지 창 버튼에 대한 결과
        answer = message.exec_()


# 두번째 탭
class SettingTap(QWidget):

    # 사용할 위젯 생성
    def __init__(self):
        super().__init__()

        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider_text = QLineEdit(str(volume))
        self.volume_checkbox = QCheckBox('음소거')
        self.volume_save = 0

        self.fps_slider = QSlider(Qt.Horizontal, self)
        self.fps_slider_text = QLineEdit(str(fps))

        self.r_but = QRadioButton('음향', self)
        self.r_but2 = QRadioButton('음향과 메시지 창', self)

        self.back_but = QPushButton()

        self.timer = QTimer()

        self.initUI()

    def initUI(self):
        groupStyle = "QGroupBox { " \
                     "font-family: '나눔바른펜'; font-size: 12pt; font-weight: bold; color: #e1effa; }"

        sliderStyle = "QSlider { padding: 10px 10px; }" \
                      "QSlider::sub-page:horizontal { " \
                      "background: #99ddff; " \
                      "border: 0px solid; border-radius: 1px; }"

        # 음향에 관한 그룹 생성 및 스타일 설정
        volume_group = QGroupBox('음량')
        volume_group.setStyleSheet(groupStyle)

        # 음향 크기에 관한 슬라이더,텍스트, 음소거 버튼 상세 설정
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.setSliderPosition(volume)
        self.volume_slider.valueChanged.connect(lambda x: self.setVolume('slider'))
        self.volume_slider.setStyleSheet(sliderStyle +
                                         "QSlider::groove:horizontal {" \
                                         "background: #cccccc; position: absolute; top: 7px; bottom: 7px; }" \
                                         "QSlider::handle:horizontal { " \
                                         "width: 8px; background: white; margin: -13px 0px;" \
                                         "border: 1px solid #232d40; border-radius: 4px; }")

        self.volume_slider_text.editingFinished.connect(lambda: self.setVolume('text'))
        self.volume_slider_text.setStyleSheet("background-color: #cccccc; color: #e1effa"
                                              "margin: 10px 2px")

        self.volume_checkbox.stateChanged.connect(self.mute)
        self.volume_checkbox.setStyleSheet("QCheckBox { "
                                           "font-family: '나눔바른펜'; font-size: 10pt; font-weight: bold; color: #e1effa; }")

        # FPS에 관한 그룹
        FPS_group = QGroupBox('프레임')
        FPS_group.setStyleSheet(groupStyle)

        # FPS에 관한 슬라이더, 텍스트 상세 설정
        self.fps_slider.setRange(20, 80)
        self.fps_slider.setTickPosition(QSlider.TicksBelow)
        self.fps_slider.setTickInterval(10)
        self.fps_slider.setSliderPosition(fps)
        self.fps_slider.valueChanged.connect(lambda x: setSliderFPS(self.fps_slider, self.fps_slider_text, self.timer))
        self.fps_slider.setStyleSheet(sliderStyle +
                                      "QSlider::groove:horizontal {" \
                                      "background: #cccccc; position: absolute; top: 11px; bottom: 11px; }" \
                                      "QSlider::handle:horizontal { " \
                                      "width: 8px; background: white; margin: -8px 0px;" \
                                      "border: 1px solid #232d40; border-radius: 4px; }")

        self.fps_slider_text.editingFinished.connect(lambda: pressEnter(self.fps_slider, self.fps_slider_text))
        self.fps_slider_text.setStyleSheet("background-color: #cccccc; color: #e1effa"
                                           "margin: 10px 2px")

        self.r_but.setChecked(True)
        self.r_but.toggled.connect(self.changeMode)
        self.r_but.setStyleSheet("QRadioButton { "
                                 "font-family: '나눔바른펜'; font-size: 10pt; font-weight: bold; color: #e1effa; }")
        self.r_but2.setStyleSheet("QRadioButton { "
                                  "font-family: '나눔바른펜'; font-size: 10pt; font-weight: bold; color: #e1effa; }")

        # TODO 사진다시 찍기라는 텍스터 넣고 묶어주기..
        self.back_but.setFixedSize(96, 96)
        self.back_but.setIcon(QIcon('./image/take-a-picture.png'))
        self.back_but.setIconSize(QSize(54, 54))
        # self.back_but.setLayoutDirection(Qt.LeftToRight)
        self.back_but.released.connect(self.confirmMassage)
        self.back_but.setStyleSheet("QPushButton  {border: 2px solid #cccccc; border-radius: 36px;"
                                    "background-color: #cccccc; "
                                    "text-align: bottom;}"
                                    "QPushButton:pressed { background-color: #8c8c8c; }")

        # 슬라이더 그룹에 위젯 배치
        volume_hbox = QHBoxLayout()
        volume_hbox.addWidget(self.volume_slider, 9)
        volume_hbox.addWidget(self.volume_slider_text, 1)

        volume_vbox = QVBoxLayout()
        volume_vbox.addLayout(volume_hbox)
        volume_vbox.addWidget(self.volume_checkbox)
        volume_group.setLayout(volume_vbox)

        # FPS그룹에 위젯 배치
        fps_hbox = QHBoxLayout()
        fps_hbox.addWidget(self.fps_slider, 9)
        fps_hbox.addWidget(self.fps_slider_text, 1)
        FPS_group.setLayout(fps_hbox)

        # 위의 두 그룹을 레이아웃에 배치
        vbox = QVBoxLayout()
        vbox.addWidget(volume_group, 1)
        vbox.addWidget(FPS_group, 1)

        radio_group = QGroupBox('알람 방법')
        radio_group.setStyleSheet(groupStyle)

        radio_vbox = QVBoxLayout()
        radio_vbox.addWidget(self.r_but)
        radio_vbox.addWidget(self.r_but2)
        radio_group.setLayout(radio_vbox)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(radio_group, 1)
        vbox2.addWidget(self.back_but, 1, Qt.AlignCenter)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox, 3)
        hbox.addLayout(vbox2, 1)

        self.setLayout(hbox)

    def setVolume(self, mode):
        if mode == "slider":
            setSliderVolume(self.volume_slider, self.volume_slider_text)
        elif mode == "text":
            pressEnter(self.volume_slider, self.volume_slider_text)

    # 음소거 버튼을 위한 함수, 누르면 비활성화/활성화가 된다.
    def mute(self):
        global volume

        if self.volume_checkbox.isChecked():
            self.volume_save = volume
            self.volume_slider.setValue(0)

            self.volume_slider.setEnabled(False)
            self.volume_slider_text.setEnabled(False)

        else:
            volume = self.volume_save
            self.volume_slider.setValue(volume)

            self.volume_slider.setEnabled(True)
            self.volume_slider_text.setEnabled(True)

    def changeMode(self):
        global isOnlySound
        isOnlySound = self.r_but.isChecked()

    def confirmMassage(self):
        self.timer.stop()

        # 메세지 창 생성 및 세부 설정
        message = QMessageBox()
        message.setWindowIcon(QIcon('./image/fairy-32.png'))
        message.setWindowTitle("확인")
        message.setText("사진을 다시 찍으시겠습니까?")
        message.setIcon(QMessageBox.Question)
        message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        message.setDefaultButton(QMessageBox.No)
        message.setStyleSheet("QMessageBox { background-color: #232d40;}"
                              "QMessageBox QLabel { "
                              "padding: 20px 5px 5px 5px;"
                              "font-family: '나눔바른펜'; font-size: 12pt; color: #e1effa; }"
                              "QMessageBox QPushButton { "
                              "background-color: #cccccc; margin: 5px; padding: 5px 15px 5px 15px; "
                              "font-family: '나눔고딕'; font-size: 10pt; font-weight: bold; color: #232d40"
                              "border: 2px solid #232d40; border-radius: 5px; }"
                              "QMessageBox QPushButton:pressed { background-color: #8c8c8c; }")

        # 메세지 창 버튼에 대한 결과
        answer = message.exec_()

        if answer == QMessageBox.Yes:  # 확인 버튼을 눌렀다면 현재 창을 숨기고 다른 창을 보인다.
            mainShowSetting()

            moniterView.hide()
            mainView.show()
        else:  # 취소 버튼을 눌렀다면 타이머를 다시 시작한다.
            self.timer.start(1000 // fps)


# 알림 창
class AlarmWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.fairy = QLabel()
        self.fairy_text = QLabel("척추의 요정")

        self.warning_text = QLabel("안녕! 나는 척추의 요정!")

        self.timer = QTimer()  # 타이머 (스스로 꺼지는 기간)
        self.audio = mixer

        self.initUI()

    def initUI(self):
        self.fairy.setPixmap(
            QPixmap('./image/fairy-256.png').scaled(
                64,
                64,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation))
        self.fairy.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.fairy.setMargin(5)

        self.fairy_text.setFont(QFont("나눔바른펜", 14, 100))
        self.fairy_text.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.warning_text.setFont(QFont("나눔바른펜", 12, 100))
        self.warning_text.setAlignment(Qt.AlignCenter)

        self.timer.timeout.connect(self.disappear)

        self.audio.init()

        vbox = QVBoxLayout()
        vbox.addWidget(self.fairy, 3)
        vbox.addWidget(self.fairy_text, 2)
        vbox.setSpacing(0)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox, 1)
        hbox.addWidget(self.warning_text, 3)
        hbox.setSpacing(0)
        hbox.setContentsMargins(10, 10, 10, 10)

        container = QWidget()
        container.setObjectName('container')
        # container.setStyleSheet("QWidget { "
        container.setStyleSheet("#container { "
                                "background-color: #77cccccc;"
                                "border: 2px solid #77232d40; border-radius: 5px; }")
        container.setLayout(hbox)

        box = QHBoxLayout()
        box.addWidget(container)
        box.setAlignment(Qt.AlignCenter)

        self.setLayout(box)

        # 창 설정
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(screen.width() - 500, 170, 500, 170)
        self.setFixedSize(500, 170)

    def showEvent(self, a0: QShowEvent) -> None:
        self.timer.start(8000)

        ran = random.randint(1, 3)
        self.warning_text.setText(fairyScript.getScript(ran))

        self.audio.music.load("./sound/WindowsError.mp3")

        self.audio.music.set_volume(volume / 100)
        self.audio.music.play()

    def hideEvent(self, a0: QHideEvent) -> None:
        if not moniterView.analyzeTap.isHidden():
            moniterView.analyzeTap.w_alarm_timer.start(5000)

    def disappear(self):
        self.hide()
