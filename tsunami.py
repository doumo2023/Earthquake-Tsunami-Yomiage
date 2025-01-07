import requests
import time

# 表示済みのIDを追跡するセット
seen_ids = set()

def speak_bouyomi(text='ゆっくりしていってね', voice=0, volume=-1, speed=-1, tone=-1):
    try:
        res = requests.get(
            'http://localhost:50080/Talk',
            params={
                'text': text,
                'voice': voice,
                'volume': volume,
                'speed': speed,
                'tone': tone
            }
        )
        return res.status_code
    except Exception as e:
        print(f"棒読みちゃんへの送信中にエラーが発生しました: {e}")
        return None

def fetch_tsunami_data():
    url = "https://api-v2-sandbox.p2pquake.net/v2/history"
    params = {
        "codes": "552",
        "limit": 1
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:  # データが空配列の場合
            return  # 読み上げずに終了

        for item in data:
            # IDを取得
            item_id = item.get("id")
            
            # すでに表示済みのIDはスキップ
            if item_id in seen_ids:
                continue

            # 初めてのIDとしてセットに追加
            seen_ids.add(item_id)

            if item.get("cancelled", False):
                message = "津波予報が解除されました。"
                print(message)
                speak_bouyomi(message)
                print("\n\n")  # idごとに2行の改行を追加
                continue  # 解除された場合はスキップ

            warning_levels = ["大津波警報", "津波警報", "津波注意報"]
            warnings = {level: [] for level in warning_levels}

            for area in item.get("areas", []):
                grade = area['grade']
                arrival_time_raw = area['firstHeight'].get('arrivalTime', '不明')
                arrival_time = arrival_time_raw
                if arrival_time != "不明" and len(arrival_time_raw.split("/")) == 3:
                    try:
                        date_part, time_part = arrival_time_raw.split(" ")
                        day = int(date_part.split("/")[-1])  # 日のみ抽出
                        hour, minute = time_part.split(":")[:2]  # 時と分を抽出
                        arrival_time = f"{day}日{hour}時{minute}分"
                    except ValueError:
                        arrival_time = "不明"

                condition = area['firstHeight'].get('condition')

                # 特殊な条件による追加メッセージ
                additional_message = ""
                if condition == "ただちに津波来襲と予測":
                    additional_message = "ただちに津波来襲と予測されます"
                elif condition == "津波到達中と推測":
                    additional_message = "津波到達中と推測されます"
                elif condition == "第１波の到達を確認":
                    additional_message = "第１波の到達を確認しました"

                # 到達予測のメッセージフォーマット
                if not additional_message and arrival_time != "不明":
                    additional_message = f"早いところで、{arrival_time}ごろ到達とみられます"

                area_info = {
                    "地域": area['name'],
                    "予想の高さ": area.get('maxHeight', {}).get('description', '不明'),
                    "到達予測": additional_message
                }

                if grade == "MajorWarning":
                    warnings["大津波警報"].append(area_info)
                elif grade == "Warning":
                    warnings["津波警報"].append(area_info)
                elif grade == "Watch":
                    warnings["津波注意報"].append(area_info)

            for grade_name in warning_levels:
                if warnings[grade_name]:
                    message_lines = [
                        f"{grade_name} が発表されました。",
                        f"{grade_name} が発表されている地域をお伝えします。"
                    ]
                    for info in warnings[grade_name]:
                        region_message = (
                            f"{info['地域']}、予想の高さ {info['予想の高さ']}、{info['到達予測']}"
                        )
                        message_lines.append(region_message)

                    full_message = "\n".join(message_lines)
                    print(full_message)
                    speak_bouyomi(full_message)

            print("\n\n")  # idごとに2行の改行を追加

    except requests.RequestException as e:
        error_message = f"エラーが発生しました: {e}"
        print(error_message)
        speak_bouyomi(error_message)

if __name__ == "__main__":
    while True:
        fetch_tsunami_data()
        time.sleep(2)
