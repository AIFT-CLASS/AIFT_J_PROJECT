# AIFT_J_PROJECT

2022-2 SSWU PROJECT  
* Artificial Intelligence in Financial Trade Project  
* 손가락 하나 까딱하지 않는 주식 거래 시스템 구축 (참고)  
 
## 현재 진행상황  

### 1. 키움 API 설치 및 환경설정  

> PyCharm, Anaconda Windows 64-Bit   
> CMD 관리자 권한 실행  
> 32bit 가상환경 set CONDA_FORCE_32BIT=1  
> PyQt5 필요  

### 2. 키움 API로 키움증권 로그인 ( ~ 2022.11.14 )  

> 계좌개설, 공동인증서  
 
 ```python 
self.get_ocx_instance()  
self.event_slots()  
self.signal_login_commConnect()  
```

### 3. 계좌번호  ( ~ 2022.11.14 )  

> 로그인 후 계좌번호 요청  

 ```python  
self.get_account_info()  
 ```

### 4. 예수금 정보 ( ~ 2022.11.15 )  

> opw 00001 : 예수금상세현황요청  
>trdata_slot 오류 해결 ( 자동로그인 필수 )  

 ```python  
self.detail_account_info()  
 ```

### 5. 계좌평가잔고내역, 보유 종목, 미체결 종목, 코스닥 개수, 일봉데이터 ( ~ 2022.11.16 )  

> 키움증권 모의투자로 로그인 후 매수 ( 체결 / 미체결되도록 매수 후 확인 완료 )  
> 싱글데이터로 정보 처리, 멀티데이터로 보유 종목 정보 처리  
> 코스닥 종목 일봉데이터 가져오기  
> 일봉데이터 가져오기 필요없으면 self.calculator_fnc()에 주석처리  

 ``` python  
self.detail_account_mystock()  
self.not_concluded_account()   
self.calculator_fnc()  
 ```  
 
### 6. 코스닥 일봉데이터 1604개 받기 완료 ( ~ 2022.11.17 )  

> 1604개 10시간 소요  

### 7. 포트폴리오로 종목 분석 - 이동평균선 비교 ( ~ 2022.11.17 ) 

> 최근의 일봉에서 고가와 저가를 이동평균선과 비교   
>> 그랜빌 4법칙 - 120일 이동평균선 사용  
> 이동평균선 가격 계산  
> 이동평균선보다 아래에 있는지 확인  
> 이동평균선보다 위에 위치하는 구간 구하기  
> 가장 최근 이동평균선 가격이 과거의 이동평균선 가격보다 높은지 확인  

### 8. 조건 통과한 종목 파일로 저장 ( ~ 2022.11.17 )

> 120일 이동평균선 사용으로 조건 통과 종목 적은 상태  
> 장이 끝나는 시점에 동작하도록 설정해야 함.

### 9. 이동평균선 120일 -> 20일로 변경 ( ~ 2022.11.21 )
> 조건 통과 종목이 매우 적은 상황이라 제대로 된 파일을 만들기 위해 파격적으로 20일로 변경  

### 10. 조건 통과 종목 파일 저장 오류 해결( ~ 2022.11.26 )  
>  드디어 해결을 했습니다 .... 


