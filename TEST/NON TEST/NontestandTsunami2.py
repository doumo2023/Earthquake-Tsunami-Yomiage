import json
import aiohttp
import asyncio
from playsound import playsound
import xml.etree.ElementTree as ET
from datetime import datetime

with open("config.json", encoding="utf-8") as f:
    CONFIG = json.load(f)

SOUNDS_DIR = CONFIG["SOUNDS_DIR"]
SOUND_FILES = CONFIG["SOUND_FILES"]
EEW_URL = CONFIG["EEW_URL"]
P2PQUAKE_URL = CONFIG["P2PQUAKE_URL"]
SCALE_TEXT = CONFIG["SCALE_TEXT"]
TSUNAMI_TEXT = CONFIG["TSUNAMI_TEXT"]
TYPE_TEXT = CONFIG["TYPE_TEXT"]

true = True
false = False

URLS = [
    "https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml",
]

async def play_sound(event_type):
    sound_file = SOUND_FILES.get(event_type)
    if sound_file:
        await asyncio.to_thread(playsound, f"{SOUNDS_DIR}/{sound_file}")

async def speak_bouyomi(text='', voice=0, volume=-1, speed=-1, tone=-1):
    params = {'text': text, 'voice': voice, 'volume': volume, 'speed': speed, 'tone': tone}
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:50080/Talk', params=params) as res:
            return res.status

async def process_eew_data(data, last_message):
    if data.get('type') == 'heartbeat': return None
    if data.get('isCancel', False): return "この緊急地震速報は取り消されました"
    message = (
        f"緊急地震速報（{'警報' if data.get('isWarn') else '予報'}）"
        f"{'最終報' if data.get('isFinal') else f'第{data.get('Serial', '不明')}報'}。"
        f"推定最大震度は{data.get('MaxIntensity', '不明')}です。"
        f"震源地は{data.get('Hypocenter', '不明')}、震源の深さは{data.get('Depth', '不明')}キロメートル、"
        f"地震の規模を示すマグニチュードは{data.get('Magunitude', '不明')}と推定されています。"
    )
    await play_sound("EEWWarning" if data.get('isWarn') else "EEWForecast")
    return message

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
    details = "\n".join(f"{info['地域']}、予想の高さ{info['予想の高さ']}、{info['到達予測']}" for info in warnings[grade_name])
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
    return SCALE_TEXT.get(str(scale), "不明")

def convert_tsunami(tsunami, foreign_tsunami=None, domestic=True):
    if foreign_tsunami is None and not domestic:
        return ""
    return TSUNAMI_TEXT.get(tsunami, "")

def convert_type(type_str):
    return TYPE_TEXT.get(type_str, "地震情報")

async def display_earthquake_info(data):
    issue = data.get('issue', {})
    eq = data.get('earthquake', {})
    text = f"{convert_type(issue.get('type', 'Other'))}。"
    t = eq.get('time', '不明')
    if t != '不明':
        date_part, time_part = t.split(" ")
        hour, minute, _ = time_part.split(":")
        text += f"{int(hour)}時{int(minute)}分ごろ地震がありました。"
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
        others = "、".join(f"{convert_scale_to_text(s)}を{'、'.join(prefs)}" for s, prefs in sorted(other.items(), reverse=True))
        text += f"また、{others}で観測しました。"
    return text

async def on_message(message):
    data = json.loads(message)
    code = data.get('code')
    if code == 551:
        await display_earthquake_info(data)
    elif code == 552:
        await process_tsunami_data([data])

async def on_eew_message(message, last):
    data = json.loads(message)
    new_msg = await process_eew_data(data, last)
    if new_msg:
        print(new_msg)
        await speak_bouyomi(new_msg)
    return new_msg or last

async def ws_handler(url, handler, last=None):
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            last = await handler(msg.data, last)
        except Exception as e:
            print(f"WebSocket error: {e}")
            await asyncio.sleep(5)

async def fetch_xml(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"Error fetching {url}: {response.status}")
                return None

def strip_ns(elem):
    for e in elem.iter():
        if '}' in e.tag:
            e.tag = e.tag.split('}', 1)[1]

def format_observed_time(time_str):
    try:
        dt = datetime.fromisoformat(time_str)
        return f"{dt.day}日{dt.hour}時{dt.minute}分"
    except Exception as e:
        return time_str

def fetch_and_parse_individual_xml(xml_data):
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print("XML parse error:", e)
        return None

    strip_ns(root)
    tsunami_info = []

    tsunami_elem = root.find(".//Tsunami")
    if tsunami_elem is not None:
        observation = tsunami_elem.find("Observation")
        if observation is not None:
            for item in observation.findall("Item"):
                area_name = item.find("Area/Name").text if item.find("Area/Name") is not None else "不明"
                for station in item.findall("Station"):
                    station_name = station.find("Name").text if station.find("Name") is not None else "不明"
                    max_time = station.find("MaxHeight/DateTime").text if station.find("MaxHeight/DateTime") is not None else ""
                    arrival_time = station.find("FirstHeight/ArrivalTime").text if station.find("FirstHeight/ArrivalTime") is not None else ""
                    observed_time = max_time if max_time != "" else (arrival_time if arrival_time != "" else "不明")
                    tsunami_height_elem = station.find("MaxHeight/TsunamiHeight")
                    tsunami_height = None
                    condition = None
                    if tsunami_height_elem is not None:
                        tsunami_height = tsunami_height_elem.attrib.get("description", None)
                        condition = tsunami_height_elem.attrib.get("condition", None)
                        if tsunami_height:
                            tsunami_height = tsunami_height.translate(str.maketrans(
                                'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ１２３４５６７８９０．',
                                'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890.'
                            ))
                    condition_elem = station.find("MaxHeight/Condition")
                    if not tsunami_height and condition_elem is not None:
                        tsunami_height = condition_elem.text if condition_elem.text else None
                    info = {
                        "kind": "津波観測",
                        "observed_time": observed_time,
                        "height": tsunami_height,
                        "station": station_name,
                        "area": area_name,
                        "condition": condition
                    }
                    tsunami_info.append(info)
    return tsunami_info

def parse_event_links(xml_data):
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print("XML parse error:", e)
        return {"tsunami": [], "long_period": []}
    strip_ns(root)
    event_links = {"tsunami": [], "long_period": []}
    for entry in root.findall("./entry"):
        title = entry.find("title").text
        link = entry.find("link").attrib.get("href")
        if "VTSE51" in link:
            event_links["tsunami"].append(link)
        elif "VXSE62" in link:
            event_links["long_period"].append(link)
    return event_links

def extract_height_value(height_str):
    try:
        if "m以上" in height_str:
            return float(height_str.replace("m以上", ""))
        return float(height_str.replace("m", ""))
    except ValueError:
        return -1
    
async def process_long_period_motion(xml_data):
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print("XML parse error:", e)
        return None

    strip_ns(root)
    long_period_info = {}

    for info in root.findall(".//Information[@type='長周期地震動に関する観測情報（細分区域）']"):
        for item in info.findall("Item"):
            kind_name = item.find("Kind/Name").text if item.find("Kind/Name") is not None else "不明"
            for area in item.findall("Areas/Area"):
                area_name = area.find("Name").text if area.find("Name") is not None else "不明"
                if area_name not in long_period_info:
                    long_period_info[area_name] = []
                long_period_info[area_name].append(kind_name)

    for area_name, kinds in long_period_info.items():
        kinds_text = "、".join(kinds)
        message = f"先ほどの地震により長周期地震動を観測しました。{kinds_text}を{area_name}で観測しました。"
        print(message)
        asyncio.create_task(speak_bouyomi(message))
        await play_sound("SeismicWarning")

    return long_period_info

last_tsunami_info = None
last_long_period_info = None

async def process_network_data():
    global last_tsunami_info, last_long_period_info
    while True:
        all_tsunami_info = []
        all_long_period_info = []
        
        for url in URLS:
            xml_data = await fetch_xml(url)
            if not xml_data:
                continue

            event_links = parse_event_links(xml_data)
            
            for link in event_links["tsunami"]:
                individual_xml = await fetch_xml(link)
                if individual_xml:
                    tsunami_info = fetch_and_parse_individual_xml(individual_xml)
                    if tsunami_info:
                        all_tsunami_info.extend(tsunami_info)

            for link in event_links["long_period"]:
                long_period_xml = await fetch_xml(link)
                if long_period_xml:
                    long_period_info = await process_long_period_motion(long_period_xml)
                    if long_period_info:
                        all_long_period_info.extend(long_period_info)

        sorted_tsunami_info = sorted(
            all_tsunami_info, 
            key=lambda x: extract_height_value(x['height']), 
            reverse=True
        )

        if sorted_tsunami_info:
            if sorted_tsunami_info == last_tsunami_info:
                await asyncio.sleep(60)
                continue

            last_tsunami_info = sorted_tsunami_info

            header_message = "津波観測情報。沿岸で津波を観測しています。観測地点と観測時刻、観測した津波の最大波をお伝えします。"
            print(header_message)
            await speak_bouyomi(header_message)
            await play_sound("Observation")

            for info in sorted_tsunami_info:
                formatted_time = format_observed_time(info['observed_time']) if info['observed_time'] != "不明" else "不明"
                height_message = info['height']
                condition_message = f"、{info['condition']}" if info['condition'] else ""
                message = f"{info['station']}、{formatted_time}、{height_message}{condition_message}。"
                print(message)
                await speak_bouyomi(message)

        if all_long_period_info:
            if all_long_period_info == last_long_period_info:
                await asyncio.sleep(60)
                continue

            last_long_period_info = all_long_period_info

        await asyncio.sleep(60)

async def main():
    await asyncio.gather(
        ws_handler(EEW_URL, on_eew_message),
        ws_handler(P2PQUAKE_URL, lambda msg, _: on_message(msg)),
        process_network_data()
    )

if __name__ == '__main__':
    asyncio.run(main())