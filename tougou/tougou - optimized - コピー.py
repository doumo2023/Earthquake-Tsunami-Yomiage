import json
import aiohttp
import asyncio
from playsound import playsound
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

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

executor = ThreadPoolExecutor(max_workers=10)

async def play_sound(event_type):
    sound_file = SOUND_FILES.get(event_type)
    if sound_file:
        await asyncio.get_event_loop().run_in_executor(
            executor, lambda: playsound(f"{SOUNDS_DIR}/{sound_file}")
        )

async def speak_bouyomi(text, voice=0, volume=-1, speed=-1, tone=-1):
    params = {'text': text, 'voice': voice, 'volume': volume, 'speed': speed, 'tone': tone}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:50080/Talk', params=params, timeout=2) as res:
                return res.status == 200
    except aiohttp.ClientError as e:
        print(f"棒読みちゃんエラー: {e}")
        return False

async def process_eew_data(data, last_message):
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
    return message if message != last_message else await play_sound("EEWWarning" if data.get('isWarn') else "EEWForecast") or None

def parse_arrival_time(arrival_raw):
    if arrival_raw == "不明":
        return ""
    try:
        date_part, time_part = arrival_raw.split(" ")
        day = int(date_part.split("/")[-1])
        hour, minute = map(int, time_part.split(":")[:2])
        return f"早いところで、{day}日{hour}時{minute}分ごろ到達とみられます"
    except ValueError:
        return ""

def format_warning_message(warnings, grade_name):
    details = "\n".join(
        f"{info['地域']}、予想の高さ{info['予想の高さ']}、{info['到達予測']}" for info in warnings[grade_name]
    )
    return f"津波情報。{grade_name}が発表されました。\n{grade_name}が発表されている地域をお伝えします。\n{details}\n"

async def process_tsunami_data(data):
    warning_levels = ["大津波警報", "津波警報", "津波注意報"]
    grade_map = {"MajorWarning": "大津波警報", "Warning": "津波警報", "Watch": "津波注意報"}
    condition_map = {
        "ただちに津波来襲と予測": "ただちに津波来襲と予測されます",
        "津波到達中と推測": "津波到達中と推測されます",
        "第１波の到達を確認": "第１波の到達を確認しました"
    }
    messages = []
    for item in sorted(data, key=lambda x: x.get('time', ''), reverse=True):
        if item.get("cancelled"):
            messages.append("津波情報。津波予報が解除されました。\n")
            await play_sound("Tsunamicancel")
            continue
        warnings = {level: [] for level in warning_levels}
        for area in item.get("areas", []):
            grade = grade_map.get(area.get('grade', ''), '')
            arrival = parse_arrival_time(area.get('firstHeight', {}).get('arrivalTime', '不明'))
            condition = condition_map.get(area.get('firstHeight', {}).get('condition', ''), arrival)
            warnings[grade].append({
                "地域": area.get('name', '不明'),
                "予想の高さ": area.get('maxHeight', {}).get('description', '不明'),
                "到達予測": condition
            })
        for level in warning_levels:
            if warnings[level]:
                messages.append(format_warning_message(warnings, level))
    if messages:
        combined_message = "".join(messages)
        print(combined_message)
        await speak_bouyomi(combined_message)
        await play_sound("Tsunami")

def convert_scale_to_text(scale):
    return {
        10: "震度1", 20: "震度2", 30: "震度3", 40: "震度4",
        45: "震度5弱", 46: "震度5弱以上と推定", 50: "震度5強",
        55: "震度6弱", 60: "震度6強", 70: "震度7"
    }.get(scale, "不明")

def convert_tsunami(tsunami, foreign_tsunami=None, domestic=True):
    if foreign_tsunami is None and not domestic:
        return ""
    return {
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
    }.get(tsunami, "")

def convert_type(type_str):
    return {
        "ScalePrompt": "震度速報",
        "Destination": "震源に関する情報",
        "ScaleAndDestination": "地震情報",
        "DetailScale": "地震情報",
        "Foreign": "遠地地震情報",
        "Other": "地震情報"
    }.get(type_str, "地震情報")

async def display_earthquake_info(data):
    issue = data.get('issue', {})
    eq = data.get('earthquake', {})
    text = f"{convert_type(issue.get('type', 'Other'))}。"
    t = eq.get('time', '不明')
    if t != '不明':
        dt = datetime.strptime(t, '%Y/%m/%d %H:%M:%S')
        text += f"{dt.hour}時{dt.minute}分ごろ地震がありました。"
    hypocenter = eq.get('hypocenter', {})
    if name := hypocenter.get('name'):
        text += f"震源地は{name}、"
    if (depth := hypocenter.get('depth', -1)) >= 0:
        text += f"震源の深さは{'ごく浅い' if depth == 0 else f'{depth}キロメートル'}。"
    if (magnitude := hypocenter.get('magnitude', -1)) >= 0:
        text += f"地震の規模を示すマグニチュードは{magnitude:.1f}と推定されています。"
    text += convert_tsunami(eq.get('domesticTsunami', ''), domestic=True)
    foreign = eq.get('foreignTsunami', None)
    if foreign not in [None, "Unknown"]:
        text += convert_tsunami(foreign, domestic=False)
    if pts := data.get('points', []):
        text += format_points_info(pts)
    print(text)
    await speak_bouyomi(text)
    await play_sound(issue.get('type', 'Other'))

def format_points_info(points):
    max_scale_region = {}
    for point in points:
        scale = point.get('scale', -1)
        if scale > 0:
            pref = point.get('pref', '不明')
            max_scale_region[pref] = max(max_scale_region.get(pref, 0), scale)
    if not max_scale_region:
        return ""
    max_scale = max(max_scale_region.values())
    areas_max = "、".join(pref for pref, s in max_scale_region.items() if s == max_scale)
    text = f"最大{convert_scale_to_text(max_scale)}を{areas_max}で観測しました。"
    other = {}
    for pref, s in max_scale_region.items():
        if s < max_scale:
            other.setdefault(s, []).append(pref)
    if other:
        others = "、".join(
            f"{convert_scale_to_text(s)}を{'、'.join(prefs)}" for s, prefs in sorted(other.items(), reverse=True)
        )
        text += f"また、{others}で観測しました。"
    return text

async def on_message(ws, message):
    data = json.loads(message)
    code = data.get('code')
    if code == 551:
        await display_earthquake_info(data)
    elif code == 552:
        await process_tsunami_data([data])

def on_error(ws, error):
    print(f"WebSocket error: {error}")

async def run_websocket(url, handler):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await handler(ws, msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    on_error(ws, msg.data)

async def main():
    urls = [
        "wss://ws-api.wolfx.jp/jma_eew",
        "wss://api.p2pquake.net/v2/ws"
    ]
    await asyncio.gather(*(run_websocket(url, on_message) for url in urls))

if __name__ == "__main__":
    asyncio.run(main())
