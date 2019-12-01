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

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pygame import mixer

import camera
import posePainter


class MainView(object):
    pass


class MoniterView(object):
    pass


cameraObject: camera.ImageAnalyzer # 카메라 객체
mainView: MainView  # 메인화면 객체 (지역변수로 사용하니 함수가 종료되면서 사라져서 임시적 조치로 여기에 정의)
moniterView: MoniterView    # 탭 화면 객체

fps: int = 40   # FPS값
volume: int = 50    # 음향 크기


# 텍스트로 값을 바꿀 때 불리는 함수
def pressEnter(slider, text):
    textValue = text.text()

    #음수 값에 대한 예외처리
    temp = textValue
    if temp[0] == '-':
        temp = temp[1:]

    #넣은 값이 숫자인지 확인
    if not temp.isdecimal():
        text.setText(str(fps))
        return

    textValue = int(textValue)
    minValue = slider.minimum()
    maxValue = slider.maximum()

    # 아래의 코드로도 슬라이더 값을 바꾸는 것이기 때문에
    # 자동으로 setSlider 함수가 불린다.
    if textValue < minValue:    # 슬라이더의 최소값보다 작은 경우
        slider.setValue(minValue)
        text.setText(str(minValue))
    elif textValue > maxValue:  # 슬라이더의 최대값보다 큰 경우
        slider.setValue(maxValue)
        text.setText(str(maxValue))
    else:                       # 적정한 값의 경우
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


#로딩 화면
class SplashView(QWidget):

    def __init__(self):
        super().__init__()

        self.logo_label = QLabel()  # 로고
        self.logo_text = QLabel('SpineAnalyzer')  # 로고 텍스트

        self.timer = QTimer()   #타이머 (로딩 화면에 머무르는 최소 기간)

        self.initUI()

    def initUI(self):
        #로고와 로고 텍스트, 타이머 설정
        self.logo_label.setPixmap(
            QPixmap('./image/broken-neck.png').scaled(
                256,
                256,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignCenter)

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
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #232d40")
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(screen.width() // 2 - 400, screen.height() // 2 - 200, 800, 400)
        self.setFixedSize(800, 400)

    #로딩이 끝나면 알아서 이 창을 닫고 메인 화면으로 전환이 되도록 한다.
    def startInit(self):
        global mainView

        self.timer.stop()
        mainView = MainView()
        mainView.timer.start(1000 // fps)  # 단위 : 마이크로세컨드
        mainView.show()

        self.close()


#메인 화면
class MainView(QWidget):

    def __init__(self):
        global moniterView

        super().__init__()

        moniterView = MoniterView()

        self.camera_label = QLabel()    # 카메라로 찍는 영상이 보이는 라벨
        self.camera_but = QPushButton() # 카메라 영상의 갱신을 멈추는 버튼

        #FPS에 관한 위젯들
        self.fps_text = QLabel("FPS")
        self.slider = QSlider(Qt.Vertical, self) 
        self.slider_text = QLineEdit(str(fps))

        self.timer = QTimer()   # 카메라 영상을 갱신할 때 사용하는 타이머

        self.isface = False     # 카메라에 얼굴이 탐색 되었는지

        self.initUI()

    def initUI(self):
        global cameraObject

        cameraObject = camera.ImageAnalyzer()  # 카메라 객체 생성

        # 카메라 버튼에 관한 설정
        self.camera_label.setScaledContents(True)

        self.camera_but.setFixedSize(72, 72)
        self.camera_but.setIcon(QIcon('./image/camera.png'))
        self.camera_but.setIconSize(QSize(36, 36))
        self.camera_but.released.connect(self.confirmMassage)
        self.camera_but.setStyleSheet("QPushButton  {border: 2px solid #cccccc; border-radius: 36px;"
                                      "background-color: #cccccc; }"
                                      "QPushButton:pressed { background-color: #8c8c8c; }")

        # FPS 라벨, 슬라이더, 텍스트 상세 설정
        self.fps_text.setFont(QFont('나눔바른고딕', 10, 50))
        self.fps_text.setStyleSheet("color: #232d40; margin: 10px 0px 0px 0px;")
        self.fps_text.setAlignment(Qt.AlignCenter)

        self.slider.setRange(20, 80)
        self.slider.setTickPosition(QSlider.TicksRight)
        self.slider.setTickInterval(5)
        self.slider.setSliderPosition(fps)
        self.slider.setFixedHeight(self.height() * 6 // 10)
        self.slider.valueChanged.connect(lambda x: setSliderFPS(self.slider, self.slider_text, self.timer))
        self.slider.setStyleSheet("QSlider { padding: 10px 10px; }"
                                  "QSlider::groove:vertical {"
                                  "background: #cccccc; position: absolute; left: 11px; right: 11px; }"
                                  "QSlider::handle:vertical { "
                                  "height: 8px; background: white; margin: 0 -8px;"
                                  "border: 1px solid #232d40; border-radius: 4px; }"
                                  "QSlider::add-page:vertical { background: #99ddff; "
                                  "border: 0px solid ; border-radius: 1px; }")

        self.slider_text.editingFinished.connect(lambda: pressEnter(self.slider, self.slider_text))
        self.slider_text.setStyleSheet("background-color: #cccccc; color: #e1effa"
                                       "margin: 10px 2px")

        # 카메라 타이머 설정
        self.timer.timeout.connect(self.showImage)
        self.timer.stop()

        # 텍스트들을 모아놓을 그룹 세부 설정
        guideBox = QGroupBox('사용 방법')
        # 아 드럽게 어렵네..
        guideBox.setStyleSheet("QGroupBox { "
                               "margin: 15px; margin-top: 20px; padding-top: 5px; "
                               "border: 2px solid #e1effa; border-radius: 5px; "
                               "font-family: '나눔바른펜'; font-size: 15pt; font-weight: bold; color: #e1effa; }"
                               "QGroupBox:title { "
                               "subcontrol-origin: margin; subcontrol-position: top center; "
                               "padding: 5px 5px 5px 5px; }")

        # 사용 설병을 명세한 텍스트
        guideText1 = QLabel('1. 노트북 카메라 혹은 웹캠을\n '
                            '   사용가능한 상태로 설정해주세요.')
        guideText2 = QLabel('2. 얼굴이 인식되는 상태로\n'
                            '   정면 사진을 찍어주세요.')
        guideText3 = QLabel('3. 자신의 자세를 실시간으로\n'
                            '   확인하세요.')
        guideText4 = QLabel('-TIP-')
        guideText5 = QLabel('1. 오른쪽 슬라이더로 FPS를 조절하세요.')
        guideText6 = QLabel('2. 무슨 말을 넣을까..')
        guideText7 = QLabel('3. 설정 탭에서 소리 크기와 알람 종류를\n'
                            '   조절할 수 있습니다.')

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

        # 그룹에 배경 색상을 지정하지 못하는 문제로 
        # 위젯에 배경을 설정하고 그 위젯을 그룹에 넣는 것으로 해결..;
        container = QWidget()
        container.setStyleSheet("background-color: #e1effa")

        # 카메라에 관한 위젯 배치
        box = QVBoxLayout()
        box.addWidget(self.camera_but)
        box.setAlignment(Qt.AlignHCenter)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.camera_label)
        vbox2.addLayout(box)
        vbox2.setAlignment(Qt.AlignHCenter)
        
        #FPS에 관한 위젯 배치
        vbox3 = QVBoxLayout()
        vbox3.addWidget(self.fps_text)
        vbox3.addWidget(self.slider)
        vbox3.addWidget(self.slider_text)

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
        self.setWindowTitle('SpineAnalyzer')
        self.setWindowIcon(QIcon('./image/broken-neck.png'))
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(screen.width() // 2 - 400, screen.height() // 2 - 200, 800, 400)
        self.setFixedSize(800, 400)

    # 메시지 박스가 나오면서 동영상이 멈추고 확인 버튼을 누르면 다음 창이 뜬다.
    def confirmMassage(self):
        self.timer.stop()

        # 메세지 창 생성 및 세부 설정
        message = QMessageBox()
        message.setWindowIcon(QIcon('./image/broken-neck.png'))
        message.setStyleSheet("QMessageBox { background-color: #232d40;}"
                              "QMessageBox QLabel { "
                              "padding: 20px 5px 5px 5px;"
                              "font-family: '나눔바른펜'; font-size: 12pt; color: #e1effa; }"
                              "QMessageBox QPushButton { "
                              "background-color: #cccccc; margin: 5px; padding: 5px 15px 5px 15px; "
                              "font-family: '나눔바른고딕'; font-size: 10pt; font-weight: bold; color: #232d40"
                              "border: 2px solid #232d40; border-radius: 5px; }"
                              "QMessageBox QPushButton:pressed { background-color: #8c8c8c; }")
        message.setWindowFlags(Qt.WindowTitleHint)

        if not self.isface:
            message.setWindowTitle("Warning")
            message.setText("얼굴이 인식되지 않았습니다.\n다시 찍어주세요.")
            message.setIcon(QMessageBox.Warning)
            message.setStandardButtons(QMessageBox.Yes)
            message.setDefaultButton(QMessageBox.Yes)

            message.exec_()

            self.timer.start(1000 // fps)

        else:
            message.setWindowTitle("Confirm")
            message.setText("이 사진으로 하시겠습니까?")
            message.setIcon(QMessageBox.Question)
            message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            message.setDefaultButton(QMessageBox.No)

            #메세지 창 버튼에 대한 결과
            answer = message.exec_()

            if answer == QMessageBox.Yes:    # 확인 버튼을 눌렀다면 현재 창을 숨기고 다른 창을 보인다.
                cameraObject.setStandardPose()

                self.hide()

                moniterView.show()
            else:                           # 취소 버튼을 눌렀다면 타이머를 다시 시작한다.
                self.timer.start(1000 // fps)

    # 카메라 객체에서 이미지를 받아와서 뷰 화면에서 보이도록 한다.
    def showImage(self):
        status, frame = cameraObject.setFrame()

        if status == 0:         # 이미지가 반환되지 않았을 때
            pix = QPixmap('./image/disconnected').scaled(
                128,
                128,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation)
            self.camera_label.setPixmap(pix)

        elif status in [1, 2]:  # 이미지가 성공적으로 반환되었을 때
            qImg = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pix = QPixmap.fromImage(qImg).scaled(
                self.width(),
                self.height(),
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

        self.analyzeTap = AnalyzerTap()
        self.settingTap = SettingTap()

        self.setStyleSheet("QDialog { background-color: #232d40;}")
        self.initUI()

    def initUI(self):
        # 탭을 넣을 위젯 생성 및 세부 설정
        tabs = QTabWidget() 
        tabs.setMovable(True)
        tabs.setStyleSheet("QTabWidget::pane { background-color: #232d40;"
                           "border: 2px solid #e1effa; border-radius: 4px; border-top-left-radius: 0px; }"
                           "QTabBar::tab {"
                           # "background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.3 #232d40, stop: 1.0 #e1effa);"
                           "border: 2px solid #e1effa; border-bottom-color: #232d40;"
                           "background: #232d40;"
                           "font-family: '나눔바른고딕'; font-size: 8pt; font-weight: bold; color: #e1effa;"
                           "border-top-left-radius: 4px; border-top-right-radius: 4px;"
                           "min-width: 15ex; padding: 5px; }"
                           "QTabBar::tab:!selected:hover { background: #cccccc }"
                           "QTabBar::tab:!selected { "
                           "border-bottom-color: #e1effa; border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;"
                           "margin: 5px; padding: 3px; background: #e1effa; color: #232d40;}")

        # 탭 추가
        tabs.addTab(self.analyzeTap, 'Status')
        tabs.addTab(self.settingTap, 'Setting')

        # 레이아웃 생성 및 설정
        hbox = QHBoxLayout()
        hbox.addWidget(tabs)

        self.setLayout(hbox)

        # 창 설정
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.WindowTitleHint)
        self.setWindowTitle('SpineAnalyzer')
        self.setWindowIcon(QIcon('./image/broken-neck.png'))
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, screen.height() - 350, 600, 300)
        self.setFixedSize(600, 300)


# 첫번째 탭
# TODO 애니메이션 위 라벨 추가 해야함
class AnalyzerTap(QWidget):

    def __init__(self):
        super().__init__()

        self.status_front = posePainter.FrontPose()    # 사용자 상태를 반영하는 애니메이션
        self.status_side = posePainter.SidePose()    # 사용자 상태를 반영하는 이미지

        self.x_label = QLabel('알 수 없음')
        self.y_label = QLabel('알 수 없음')
        self.z_label = QLabel('알 수 없음')
        self.turtle_label = QLabel('알 수 없음')

        mixer.init()
        self.turm = 2100

        self.timer = QTimer()
        self.alarm_timer = QTimer()

        self.initUI()

    def initUI(self):
        self.status_front.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.status_front.setAlignment(Qt.AlignCenter)

        self.status_side.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.status_side.setAlignment(Qt.AlignCenter)

        for label in [self.x_label, self.y_label, self.z_label, self.turtle_label]:
            label.setFont(QFont('나눔바른펜', 12, 50))
            label.setStyleSheet("color: #e1effa")
            label.setAlignment(Qt.AlignCenter)
            label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)

        mixer.music.load("./sound/WindowsDefault.mp3")

        self.alarm_timer.timeout.connect(self.sirenAlarm)
        self.alarm_timer.stop()

        self.timer.timeout.connect(self.analyzeImage)
        self.timer.stop()

        vbox = QVBoxLayout()
        for label in [self.x_label, self.y_label, self.z_label, self.turtle_label]:
            vbox.addWidget(label)

        hbox = QHBoxLayout()
        hbox.addWidget(self.status_side, 1)
        hbox.addWidget(self.status_front, 1)
        hbox.addLayout(vbox, 1)

        self.setLayout(hbox)

    # 창이 생겨나기전 값 초기화
    def showEvent(self, a0: QShowEvent) -> None:
        self.status_front.saveStandardShape(cameraObject.getFrontShape())

        self.timer.start(1000 // fps)
        self.alarm_timer.start(5000)

    #창이 사라지기 전 값 삭제
    def hideEvent(self, a0: QHideEvent) -> None:
        self.status_front.clear()

    def xMessage(self, x_angle):
        msg = ''

        if x_angle > 95:
            msg = "Tilt your head " + str(round(x_angle - 90, 2)) + " UP on the x axis"
        elif x_angle < 85:
            msg = "Tilt your head " + str(abs(round(x_angle - 90, 2))) + " DOWN on the x axis"
        else:
            msg = "head(x axis): OK"
        return msg

    def yMessage(self, y_angle):
        msg = ''

        if y_angle > 10:
            msg = "Tilt your head " + str(y_angle) + " LEFT on the y axis"
        elif y_angle < -10:
            msg = "Tilt your head " + str(abs(y_angle)) + " RIGHT on the y axis"
        else:
            self.alarm_timer.start(5000)
            self.turm = 2100
            msg = "head(y axis): OK"
        return msg

    def zMessage(self, z_angle):
        msg = ''

        if z_angle > 10:
            msg = "Tilt your head " + str(round(z_angle, 2)) + " LEFT on the z axis"
        elif z_angle < -10:
            msg = "Tilt your head " + str(abs(round(z_angle, 2))) + " RIGHT on the z axis"
        else:
            msg = "head(z axis): OK"
        return msg

    def turtleMessage(self, isTurtle):
        if isTurtle:
            return "now U R turtle neck."
        else:
            return "head(turtle neck): OK"

    # 자세를 분석한 결과를 메시지로 보여주는 함수
    # TODO 할 수 있으면 애니매이션으로 바꾸자.
    def analyzeImage(self):
        values, points = cameraObject.getValues()

        # print(self.alarm_timer.remainingTime())
        if values is not None:
            # TODO 상태에 따라서 컴퓨터 알림창을 띄울 수 있도록 하자.

            self.status_front.setShape(points)

            # self.x_label.setText(self.xMessage(values[0]))
            self.x_label.setText(values[0])
            self.y_label.setText(self.yMessage(values[1]))
            self.z_label.setText(self.zMessage(values[2]))
            self.turtle_label.setText(self.turtleMessage(values[3]))
        else:
            self.alarm_timer.start(5000)
            self.turm = 2100
        # print(self.alarm_timer.remainingTime())

    def sirenAlarm(self):
        if self.turm > 500:
            self.turm -= 100

        print(volume)
        mixer.music.set_volume(volume/100)
        mixer.music.play()

        self.alarm_timer.start(self.turm)


# 두번째 탭
# TODO 종료 혹은 이전 화면으로 돌아가는 버튼 필요 / 창을 가장 위에 놓을지 말지 설정하는 체크박스 만들기
class SettingTap(QWidget):

    #사용할 위젯 생성
    def __init__(self):
        super().__init__()

        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider_text = QLineEdit(str(volume))
        self.volume_checkbox = QCheckBox('MUTE')
        self.volume_save = 0

        self.fps_slider = QSlider(Qt.Horizontal, self)
        self.fps_slider_text = QLineEdit(str(fps))

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
        volume_group = QGroupBox('Volume')
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

        # 슬라이더 그룹에 위젯 배치
        volume_hbox = QHBoxLayout()
        volume_hbox.addWidget(self.volume_slider, 9)
        volume_hbox.addWidget(self.volume_slider_text, 1)

        volume_vbox = QVBoxLayout()
        volume_vbox.addLayout(volume_hbox)
        volume_vbox.addWidget(self.volume_checkbox)

        volume_group.setLayout(volume_vbox)

        # FPS에 관한 그룹
        FPS_group = QGroupBox('FPS')
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

        # FPS그룹에 위젯 배치
        fps_hbox = QHBoxLayout()
        fps_hbox.addWidget(self.fps_slider, 9)
        fps_hbox.addWidget(self.fps_slider_text, 1)
        FPS_group.setLayout(fps_hbox)

        # 위의 두 그룹을 레이아웃에 배치
        vbox = QVBoxLayout()
        vbox.addWidget(volume_group)
        vbox.addWidget(FPS_group)
        self.setLayout(vbox)

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
