import sys
import os
import time
import pandas as pd
from tqdm.auto import tqdm
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from PyQt5.QtTest import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        print("Kiwoom() class start.")

        ####### event loop를 실행하기 위한 변수 모음
        self.login_event_loop = QEventLoop() # 로그인 요청용 이벤트 루프
        self.detail_account_info_event_loop = QEventLoop() # 예수금 요청용 이벤트 루프
        self.calculator_event_loop = QEventLoop()
        #########################################

        ####### 계좌 관련된 변수
        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        self.account_num = None #계좌번호 담아줄 변수
        self.deposit = 0 #예수금
        self.use_money = 0 #실제 투자에 사용할 금액
        self.use_money_percent = 0.5 #예수금에서 실제 사용할 비율
        self.output_deposit = 0 #출력가능 금액
        self.total_profit_loss_money = 0 #총평가손익금액
        self.total_profit_loss_rate = 0.0 #총수익률(%)
        ########################################

        # 종목분석용
        self.calcul_data = []

        ####### 요청 스크린 번호
        self.screen_my_info = "2000" #계좌 관련한 스크린 번호
        self.screen_calculation_stock = "4000" #계산용 스크린 번호
        ########################################

        ######### 초기 셋팅 함수들 바로 실행
        self.get_ocx_instance() # OCX 방식을 파이썬에 사용할 수 있게 반환해 주는 함수 실행
        self.event_slots() # 키움과 연결하기 위한 시그널 / 슬롯 모음
        self.signal_login_commConnect() # 로그인 요청 함수 포함
        self.get_account_info() #계좌번호 가져오기

        self.detail_account_info() # 예수금 요청 시그널 포함
        self.detail_account_mystock() #계좌평가잔고내역 가져오기
        self.not_concluded_account() # 미체결
        self.calculator_fnc() # 코스닥갯수 - 일봉데이터 안가져오려면 주석처리하기
        #########################################

        self.read_code()

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1") # 레지스트리에 저장된 API 모듈 불러오기

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot) # 로그인 관련 이벤트
        self.OnReceiveTrData.connect(self.trdata_slot) # 트랜잭션 요청 관련 이벤트

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()") # 로그인 요청 시그널

        self.login_event_loop.exec_() # 이벤트 루프 실행

    def login_slot(self, err_code):
        print(errors(err_code)[1])

        #로그인 처리가 완료됐으면 이벤트 루프를 종료한다.
        self.login_event_loop.exit()

    def get_account_info(self):
        account_list = self.dynamicCall("GetLoginInfo(QString)", "ACCNO") # 계좌번호 반환
        account_num = account_list.split(';')[0] # a;b;c  [a, b, c]

        self.account_num = account_num

        print("계좌번호 : %s" % account_num)

    def detail_account_info(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "예수금상세현황요청", "opw00001", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "opw00018", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def not_concluded_account(self, sPrevNext="0"):
        print("미체결 종목 요청")
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):

        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "예수금")
            self.deposit = int(deposit)

            use_money = float(self.deposit) * self.use_money_percent
            self.use_money = int(use_money)
            self.use_money = self.use_money / 4

            output_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "출금가능금액")
            self.output_deposit = int(output_deposit)

            print("예수금 : %s" % self.output_deposit)

            self.stop_screen_cancel(self.screen_my_info)

            self.detail_account_info_event_loop.exit()

        elif sRQName == "계좌평가잔고내역요청":
            total_buy_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총매입금액") # 출력 : 000000000746100
            self.total_buy_money = int(total_buy_money)
            total_profit_loss_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총평가손익금액") # 출력 : 000000000009761
            self.total_profit_loss_money = int(total_profit_loss_money)
            total_profit_loss_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총수익률(%)") # 출력 : 000000001.31
            self.total_profit_loss_rate = float(total_profit_loss_rate)

            print("계좌평가잔고내역요청 싱글데이터 : %s - %s - %s" % (total_buy_money, total_profit_loss_money, total_profit_loss_rate))

            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)

            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                code = code.strip()[1:]

                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")
                buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")
                learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")

                print("종목번호: %s - 종목명: %s - 보유수량: %s - 매입가:%s - 수익률: %s - 현재가: %s" % (code, code_nm, stock_quantity, buy_price, learn_rate, current_price))

                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict[code] = {}

                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())

                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})

            print("sPreNext : %s" % sPrevNext)      # 미체결 종목 요청 결과를 받기 위한 슬롯 영역 150p
            print("계좌에 가지고 있는 종목은 %s " % rows)

            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop.exit()

        elif sRQName == "실시간미체결요청":    # 미체결 종목 요청의 데이터 반환
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)

            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목코드")

                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문상태") # 접수,확인,체결
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문가격")
                order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문구분") # -매도, +매수, -매도정정, +매수정정
                not_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "미체결수량")
                ok_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결량")

                code = code.strip()    # 미체결 종목 정보의 형 변환
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}   # 주문번호 없으면 딕셔너리 업데이트함 

                self.not_account_stock_dict[order_no].update({'종목코드': code})
                self.not_account_stock_dict[order_no].update({'종목명': code_nm})
                self.not_account_stock_dict[order_no].update({'주문번호': order_no})
                self.not_account_stock_dict[order_no].update({'주문상태': order_status})
                self.not_account_stock_dict[order_no].update({'주문수량': order_quantity})
                self.not_account_stock_dict[order_no].update({'주문가격': order_price})
                self.not_account_stock_dict[order_no].update({'주문구분': order_gubun})
                self.not_account_stock_dict[order_no].update({'미체결수량': not_quantity})
                self.not_account_stock_dict[order_no].update({'체결량': ok_quantity})

                print("미체결 종목 : %s " % self.not_account_stock_dict[order_no])

            self.detail_account_info_event_loop.exit()

        elif sRQName == "주식일봉차트조회":
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            code = code.strip()  # 여기서부터 일봉데이터 가져오기 175p 
           

            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)  # 최대 600일
            

            # data = self.dynamicCall("GetCommDataEx(QString, QString)", sTrCode, sRQName)

            for i in range(cnt):
                data = []   # 저장할 리스트

                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", sTrCode, sRQName, i, "현재가")
                value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량")
                trading_value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래대금")
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")
                start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가")
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가")
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가")

                data.append("")
                data.append(current_price.strip())
                data.append(value.strip())
                data.append(trading_value.strip())
                data.append(date.strip())
                data.append(start_price.strip())
                data.append(high_price.strip())
                data.append(low_price.strip())
                data.append("")

                self.calcul_data.append(data.copy())

            if sPrevNext == "2":
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)
            else:
                print("총 일수 %s" % len(self.calcul_data))

                pass_success = False

                # 20일 이평선을 그릴만큼의 데이터가 있는지 확인
                if self.calcul_data is None or len(self.calcul_data) < 20:
                    pass_success = False
                else:
                    # 데이터가 20일 이상 있으면,
                    total_price = 0
                    for value in self.calcul_data[:20]:
                        total_price += int(value[1])

                    moving_average_price = total_price / 20

                    # 1. 오늘자 주가가 20 이평선에 걸쳐있는지 확인
                    bottom_stock_price = False
                    check_price = None

                    if int(self.calcul_data[0][7]) <= moving_average_price <= int(self.calcul_data[0][6]):
                        print("오늘 주가가 20 이평선에 걸쳐있는지 확인")
                        bottom_stock_price = True
                        check_price = int(self.calcul_data[0][6])

                    # 2. 과거 일봉들이 20일 이평선보다 밑에 있는지 확인
                    prev_low_price = 0  # 과거 일봉 주가
                    if bottom_stock_price is True:
                        moving_average_price_prev = 0
                        price_top_moving = False    # 주가가 이평선보다 위에 위치하는가?

                        idx = 1
                        while True:
                            if len(self.calcul_data[idx:]) < 20:   # 20 있는지 계속 확인
                                print("20일치가 없음")
                                break

                            total_price = 0
                            for value in self.calcul_data[idx:20+idx]:
                                total_price += int(value[1])
                            moving_average_price_prev = total_price / 20

                            if moving_average_price_prev <= int(self.calcul_data[idx][6]) and idx <= 3:
                                print("3일 동안 주가가 이평선과 같거나 위에 있으면 조건 탈락")
                                price_top_moving = False
                                break
                            elif int(self.calcul_data[idx][7]) > moving_average_price_prev and idx > 20:
                                print("20일 이평선 위에 있는 일봉 확인")
                                price_top_moving = True
                                prev_low_price = int(self.calcul_data[idx][7])  # 이평선위의 일봉 저가 저장
                                break

                            idx += 1

                        # 해당 부분 이평선이 가장 최근 일자의 이평선 가격보다 낮은지 확인
                        if price_top_moving is True:
                            if moving_average_price > moving_average_price_prev and check_price > prev_low_price:
                                print("포착된 이평선의 가격이 오늘자(최근일자) 이평선 가격보다 낮은 것 확임됨")
                                print("포착된 부분의 일봉 저가가 오늘자 일봉의 고가보다 낮은지 확임됨")
                                pass_success = True

                if pass_success is True: # 조건에 통과한 종목 저장
                    print("조건부 통과됨")

                    code_nm = self.dynamicCall("GetMasterCodeName(QString)", code)

                    f = open("files/condition_stock.txt", "a", encoding="utf8")
                    f.write("%s\t%s\t%s\n" % (code, code_nm, str(self.calcul_data[0][1])))
                    f.close()

                elif pass_success is False:
                    print("조건부 통과 못함")

                self.calcul_data.clear()
                self.calculator_event_loop.exit()

    def stop_screen_cancel(self, sScrNo=None):       # 코스닥 종목 요청 함수 159p
        self.dynamicCall("DisconnectRealData(QString)", sScrNo) # 스크린 번호 연결 끊기

    def get_master_code_name(self, code_name):  # 종목분석, 관련 코드 모아놓기위한
        code_list = self.dynamicCall("GetMasterCodeName(QString)", code_name)
        #code_list = code_list.split(';')[:-1]
        return code_list

    # tr_dic = {
    #             'opt20005': {'001': '', '201': 'kospi200'},
    #             'opt10080': {'069500':'kodex_200', '114800':'kodex_inverse', '226490':'kodex_kospi'}
    #        }

    def calculator_fnc(self):  # 각 종목의 정보 가져오기
        for idx in range (202):
            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculation_stock) # 스크린 연결 끊기
            
            print("%s / 200 : KOSDAQ Stock Code : %s is updating... " % idx)
            self.day_kiwoom_db(code=None)

    def day_kiwoom_db(self, code="201", date=None, sPrevNext="0"):
        QTest.qWait(3600) #3.6초마다 딜레이를 준다.

        self.dynamicCall("SetInputValue(QString, QString)", "업종코드", code)
        if date != None:
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)

        #self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", sPrevNext, self.screen_calculation_stock)
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "업종일봉조회", "opt20006", sPrevNext, self.screen_calculation_stock)

        self.calculator_event_loop.exec_()

    def read_code(self):
        if os.path.exists("files/condition_stock.txt"): # 해당 경로에 파일이 있는지 체크한다.
            f = open("files/condition_stock.txt", "r", encoding="utf8")

            lines = f.readlines() #파일에 있는 내용들이 모두 읽어와 진다.
            for line in lines: #줄바꿈된 내용들이 한줄 씩 읽어와진다.
                if line != "":
                    ls = line.split("\t")

                    stock_code = ls[0]
                    stock_name = ls[1]
                    stock_price = int(ls[2].split("\n")[0])
                    stock_price = abs(stock_price)

                    self.portfolio_stock_dict.update({stock_code:{"종목명":stock_name, "현재가":stock_price}})
            f.close()