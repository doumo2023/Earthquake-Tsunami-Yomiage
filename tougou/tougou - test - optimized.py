import time
from datetime import datetime
from playsound import playsound
from websocket import WebSocketApp
import json
import requests
import threading

SOUNDS_DIR = "./Sounds"
SOUND_FILES = {
    "EEWWarning": "Eewwarning.mp3",
    "EEWForecast": "Eewforecast.mp3",
    "Tsunami": "Tsunami.mp3",
    "Tsunamicancel": "Tsunamicancel.mp3",
    "ScalePrompt": "ScalePrompt.mp3",
    "Destination": "Destination.mp3",
    "ScaleAndDestination": "Earthquake.mp3",
    "DetailScale": "Earthquake.mp3",
    "Foreign": "Foreign.mp3",
}

def play_sound(event_type):
    sound_file = SOUND_FILES.get(event_type)
    if sound_file:
        try:
            playsound(f"{SOUNDS_DIR}/{sound_file}")
        except Exception as e:
            print(f"音声再生エラー: {e}")

def speak_bouyomi(text='ゆっくりしていってね', voice=0, volume=-1, speed=-1, tone=-1):
    try:
        res = requests.get('http://localhost:50080/Talk', params={
            'text': text, 'voice': voice, 'volume': volume, 'speed': speed, 'tone': tone
        }, timeout=2)
        return res.status_code == 200
    except requests.RequestException as e:
        print(f"棒読みちゃんエラー: {e}")
        return False

def process_eew_data(data, last_message):
    if not data:
        return None
    if data.get('isCancel', False):
        return "この緊急地震速報は取り消されました"
    message = (
        f"緊急地震速報（{'警報' if data.get('isWarn') else '予報'}）"
        f"{'最終報' if data.get('isFinal') else f'第{data.get('Serial', '不明')}報'}。"
        f"推定最大震度は{data.get('MaxIntensity', '不明')}です。"
        f"震源地は{data.get('Hypocenter', '不明')}、震源の深さは{data.get('Depth', '不明')}キロメートル、"
        f"地震の規模を示すマグニチュードは{data.get('Magunitude', '不明')}と推定されています。"
    )
    if message != last_message:
        play_sound("EEWWarning" if data.get('isWarn') else "EEWForecast")
    return message if message != last_message else None

def process_tsunami_data(data):
    messages, warning_levels = [], ["大津波警報", "津波警報", "津波注意報"]
    grade_map = {"MajorWarning": "大津波警報", "Warning": "津波警報", "Watch": "津波注意報"}
    condition_map = {
        "ただちに津波来襲と予測": "ただちに津波来襲と予測されます",
        "津波到達中と推測": "津波到達中と推測されます",
        "第１波の到達を確認": "第１波の到達を確認しました"
    }
    for item in sorted(data, key=lambda x: x.get('time', ''), reverse=True):
        if item.get("cancelled", False):
            messages.append("津波情報。津波予報が解除されました。")
            play_sound("Tsunamicancel")
            continue
        warnings = {level: [] for level in warning_levels}
        for area in item.get("areas", []):
            grade = grade_map.get(area['grade'], '')
            if not grade:
                continue
            arrival_time = "不明"
            if (arrival_raw := area['firstHeight'].get('arrivalTime', '不明')) != "不明":
                try:
                    date_part, time_part = arrival_raw.split(" ")
                    hour, minute = map(int, time_part.split(":")[:2])
                    arrival_time = f"{date_part.split('/')[-1]}日{hour}時{minute}分"
                except ValueError:
                    pass
            warnings[grade].append({
                "地域": area['name'],
                "予想の高さ": area.get('maxHeight', {}).get('description', '不明'),
                "到達予測": condition_map.get(
                    area['firstHeight'].get('condition', ''),
                    f"早いところで、{arrival_time}ごろ到達とみられます" if arrival_time != "不明" else ""
                )
            })
        for grade_name in warning_levels:
            if warnings[grade_name]:
                messages.append("\n".join(
                    [f"津波情報。{grade_name} が発表されました。", f"{grade_name} が発表されている地域をお伝えします。"] +
                    [f"{info['地域']}、予想の高さ{info['予想の高さ']}、{info['到達予測']}" for info in warnings[grade_name]]
                ))
    for message in messages:
        print(message + "\n")
        speak_bouyomi(message)
        play_sound("Tsunami")

def convert_scale_to_text(scale):
    return {
        10: "震度1", 20: "震度2", 30: "震度3", 40: "震度4",
        45: "震度5弱", 46: "震度5弱以上と推定", 50: "震度5強",
        55: "震度6弱", 60: "震度6強", 70: "震度7"
    }.get(scale, "不明")

def convert_tsunami(tsunami, foreign_tsunami=None, domestic=True):
    if foreign_tsunami is None and not domestic:
        return ""
    texts = {
        "None": "この地震による津波の心配はありません。",
        "Checking": "津波の有無については現在調査中です。今後の情報に警戒してください。",
        "NonEffective": "この地震により若干の海面変動が予想されますが、津波被害の心配はありません。",
        "Watch": "この地震により、津波注意報が発表されました。",
        "Warning": "この地震により、現在津波情報等を発表中です。",
        "NonEffectiveNearby": "震源の近傍では小さな津波が発生するかもしれませんが、被害の心配はありません。",
        "WarningNearby": "震源の近傍では津波発生の可能性があります。",
        "WarningPacific": "太平洋では津波の発生の可能性があります。",
        "WarningPacificWide": "太平洋の広域で津波の可能性があります。",
        "WarningIndian": "インド洋では津波の可能性があります。",
        "WarningIndianWide": "インド洋の広域で津波の可能性があります。",
        "Potential": "一般にこの規模では津波の可能性があります。"
    }
    return texts.get(tsunami, "")

def convert_type(type_str):
    return {
        "ScalePrompt": "震度速報",
        "Destination": "震源に関する情報",
        "ScaleAndDestination": "地震情報",
        "DetailScale": "地震情報",
        "Foreign": "遠地地震情報",
        "Other": "地震情報"
    }.get(type_str, "地震情報")

def display_earthquake_info(data):
    type_info = convert_type(data.get('issue', {}).get('type', 'Other'))
    text = f"{type_info}。"
    earthquake = data.get('earthquake', {})
    time = earthquake.get('time', '不明')
    if time != '不明':
        dt = datetime.strptime(time, '%Y/%m/%d %H:%M:%S')
        text += f"{dt.hour}時{dt.minute}分ごろ地震がありました。"
    hypocenter = earthquake.get('hypocenter', {})
    if hypocenter.get('name'):
        text += f"震源地は{hypocenter['name']}、"
    if (depth := hypocenter.get('depth', -1)) >= 0:
        text += f"震源の深さは{'ごく浅い' if depth == 0 else f'{depth}キロメートル'}。"
    if (magnitude := hypocenter.get('magnitude', -1)) >= 0:
        text += f"地震の規模を示すマグニチュードは{magnitude:.1f}と推定されています。"
    text += convert_tsunami(earthquake.get('domesticTsunami', ''), domestic=True)
    foreign_tsunami = earthquake.get('foreignTsunami', None)
    if foreign_tsunami not in [None, "Unknown"]:
        text += convert_tsunami(foreign_tsunami, domestic=False)
    points = data.get('points', [])
    if points:
        max_scale_region = {}
        for point in points:
            if (scale := point.get('scale', -1)) > 0:
                pref = point.get('pref', '不明')
                max_scale_region[pref] = max(max_scale_region.get(pref, 0), scale)
        max_scale = max(max_scale_region.values(), default=0)
        if max_scale:
            areas = [pref for pref, scale in max_scale_region.items() if scale == max_scale]
            text += f"最大{convert_scale_to_text(max_scale)}を{'、'.join(areas)}で観測しました。"
        other_scales = {s: [] for s in set(max_scale_region.values()) if s < max_scale}
        for pref, scale in max_scale_region.items():
            if scale < max_scale:
                other_scales[scale].append(pref)
        if other_scales:
            text += "また、" + "、".join(
                f"{convert_scale_to_text(scale)}を{'、'.join(prefs)}"
                for scale, prefs in sorted(other_scales.items(), reverse=True)
            ) + "で観測しました。"
    print(text)
    speak_bouyomi(text)
    play_sound(data.get('issue', {}).get('type', 'Other'))

def on_message(ws, message):
    data = json.loads(message)
    if 'code' in data and data['code'] == 551:
        display_earthquake_info(data)
    elif 'code' in data and data['code'] == 552:
        process_tsunami_data([data])

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def main():
    wolfx_url = "wss://ws-api.wolfx.jp/jma_eew"
    websocket_url = "wss://api-realtime-sandbox.p2pquake.net/v2/ws"
    last_eew_message = None
    def on_eew_message(ws, message):
        nonlocal last_eew_message
        data = json.loads(message)
        if eew_message := process_eew_data(data, last_eew_message):
            print(eew_message)
            speak_bouyomi(eew_message)
            last_eew_message = eew_message

    def run_websocket(url, on_message):
        WebSocketApp(url, on_message=on_message, on_error=on_error).run_forever()

    threading.Thread(target=run_websocket, args=(wolfx_url, on_eew_message)).start()
    threading.Thread(target=run_websocket, args=(websocket_url, on_message)).start()

if __name__ == "__main__":
    main()
