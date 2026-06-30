from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import requests
import time

app = Flask(__name__)
CORS(app) # HTML과 파이썬 서버가 서로 통신할 수 있게 길을 열어줍니다.

# 디스코드 웹훅 주소 (서버가 직접 쏩니다!)
WEBHOOK_URL = "https://discord.com/api/webhooks/1520066929711120446/sAZiHZG9pRiVb9TPuOghaOoFvjoYKUtiIy1sQ2bb7tSyfnIfuE7EzM_55GB2Y99tfjF9"

# 백그라운드에서 실행될 디스코드 전송 함수
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
        print(f"[{mission_name}] 디스코드 알림 전송 완료!")
    except Exception as e:
        print(f"전송 에러: {e}")

# 브라우저에서 요청이 들어오는 출입구 (라우터)
@app.route('/start_timer', methods=['POST'])
def start_timer():
    data = request.json
    mission_name = data.get('mission_name', '알 수 없는 임무')
    duration = int(data.get('time', 0))
    mention_str = data.get('mention', '')

    print(f"요청 접수: {mission_name} / {duration}초 대기 시작...")

    # 🌟 핵심: 메인 서버를 멈추지 않고, 백그라운드 스레드로 타이머를 따로 돌립니다.
    timer_thread = threading.Timer(duration, send_discord_alert, args=[mission_name, mention_str])
    timer_thread.start()

    # 브라우저에는 즉시 "주문 잘 받았습니다!" 라고 응답해줍니다.
    return jsonify({"status": "success", "message": f"{mission_name} 타이머가 서버에 등록되었습니다."})

if __name__ == '__main__':
    # 서버 실행 (기본 포트 5000번)
    app.run(host='0.0.0.0', port=5000, debug=True)