script1 = "안녕? 나는 척추의 요정!"
script2 = "신기한 거북이구나! 음? \n미안! 사람인줄 생각도 못했어!"
script3 = "척추 수술은 2000만원만 있으면 시술이 가능하데!\n저렴한거 맞지?" # 최대 길이


def getScript(num):
    return globals()['script{}'.format(num)]
