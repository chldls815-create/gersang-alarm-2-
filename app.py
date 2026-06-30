from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import requests
import time
import json

app = Flask(__name__)
CORS(app)  # HTML과 파이썬 서버가 서로 통신할 수 있게 길을 열어줍니다.

# ================= [ 환경 설정 영역 ] =================
WEBHOOK_URL = "https://discord.com/api/webhooks/1520066929711120446/sAZiHZG9pRiVb9TPuOghaOoFvjoYKUtiIy1sQ2bb7tSyfnIfuE7EzM_55GB2Y99tfjF9"
REST_API_KEY = "1b59058000c9c27fa56dc7e509c23507"
REDIRECT_URI = "https://localhost"

# ⚠️ 중요: 최초 성공 시 받은 'refresh_token'을 여기에 꼭 넣어주세요!
# 이 토큰이 있어야 서버가 24시간 동안 죽지 않고 출입증을 자동 갱신합니다.
REFRESH_TOKEN = "at2ey84esiE8npEUdoqfwarxgHBJ1gOEAAAAAgoXNd0AAAGfGG0FhP6hmr4nKm-b"
# =====================================================

# 글로벌 변수로 현재 활성화된 출입증 관리
current_access_token = None

# 🔄 카카오 출입증(Access Token) 자동 갱신 함수
def refresh_kakao_token():
    global current_access_token, REFRESH_TOKEN
    
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": REFRESH_TOKEN
    }
    
    try:
        response = requests.post(url, data=data)
        result = response.json()
        
        if "access_token" in result:
            current_access_token = result["access_token"]
            print("🔄 [카카오] 출입증(Access Token) 자외선 갱신 완료!")
            
            # 리프레시 토큰도 가끔 갱신되므로, 새로 들어오면 업데이트
            if "refresh_token" in result:
                REFRESH_TOKEN = result["refresh_token"]
            return True
        else:
            print(f"❌ [카카오] 토큰 갱신 실패: {result}")
            return False
    except Exception as e:
        print(f"❌ [카카오] 토큰 갱신 중 서버 에러: {e}")
        return False

# 💬 카카오톡 나에게 보내기 전송 함수
def send_kakao_alert(mission_name):
    global current_access_token
    
    # 알림을 쏘기 직전에 무조건 출입증을 새로 갱신받아 안전하게 쏩니다.
    if not refresh_kakao_token():
        print("❌ [카카오] 토큰 갱신에 실패하여 카톡을 보낼 수 없습니다.")
        return

    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {current_access_token}"}
    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": f"🔔 거상 알리미\n[{mission_name}] 임무 시간이 완료되었습니다! 얼른 수령하세요.",
            "link": {"web_url": "https://chldls815-create.github.io/gersangcalendar/"}
        })
    }
    
    try:
        res = requests.post(url, headers=headers, data=payload)
        if res.status_code == 200:
            print(f"📱 [{mission_name}] 카카오톡 알림 전송 완료!")
        else:
            print(f"❌ [카카오] 카톡 전송 실패: {res.text}")
    except Exception as e:
        print(f"❌ [카카오] 전송 중 에러: {e}")

# 👾 디스코드 알림 전송 함수
def send_discord_alert(mission_name, mention_str):
    mention_text = f"<@{mention_str}> " if mention_str and mention_str != "" else ""
    if mention_str == "@everyone":
         mention_text = "@everyone "

    payload = {
        "content": f"{mention_text}🔔 **주막 임무 완료!**\n{mission_name} 임무 시간이 다 되었습니다. 얼른 게임에서 수령하세요!",
        "username": "거상 주막 알리미 (서버 구동)",
        "avatar_url": "https://via.placeholder.com/150/0984e3/ffffff?text=Server"
    }

    try:
        requests.post(WEBHOOK_URL, json=payload)
        print(f"👾 [{mission_name}] 디스코드 알림 전송 완료!")
    except Exception as e:
        print(f"❌ [디스코드] 전송 에러: {e}")

# 🔔 모든 채널(디스코드 + 카카오톡)로 알림을 쏴주는 마스터 함수
def send_all_alerts(mission_name, mention_str):
    # 백그라운드 스레드에서 두 군데로 동시에 쏩니다.
    send_discord_alert(mission_name, mention_str)
    send_kakao_alert(mission_name)

# 🌐 브라우저에서 요청이 들어오는 출입구 (라우터)
@app.route('/start_timer', methods=['POST'])
def start_timer():
    data = request.json
    mission_name = data.get('mission_name', '알 수 없는 임무')
    duration = int(data.get('time', 0))
    mention_str = data.get('mention', '')

    print(f"📥 요청 접수: {mission_name} / {duration}초 대기 시작...")

    # 메인 서버가 멈추지 않도록 백그라운드 스레드로 타이머를 따로 돌립니다.
    # 대기 시간이 끝나면 send_all_alerts 가 실행됩니다.
    timer_thread = threading.Timer(duration, send_all_alerts, args=[mission_name, mention_str])
    timer_thread.start()

    return jsonify({"status": "success", "message": f"{mission_name} 타이머가 서버에 등록되었습니다."})

if __name__ == '__main__':
    # 서버 실행 (기본 포트 5000번)
    app.run(host='0.0.0.0', port=5000, debug=True)
