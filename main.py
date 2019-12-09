import view
import sys

if __name__ == '__main__':
    app = view.QApplication(sys.argv)
    ex = view.SplashView()
    ex.show()

    answer = app.exec_()
    view.cameraObject.release()

    sys.exit(answer)
