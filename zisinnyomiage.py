import requests
import json

def fetch_latest_earthquake():
    # API URL
    url = "https://api.wolfx.jp/jma_eqlist.json"

    try:
        # データを取得
        response = requests.get(url)
        response.raise_for_status()  # HTTPエラーがある場合は例外を発生

        # JSONデータを解析
        data = response.json()

        # データが辞書形式である場合のみ処理
        if not data or not isinstance(data, dict):
            print("地震情報が見つかりませんでした。")
            return

        # No1 の地震情報を取得
        latest = data.get("No1", None)

        if latest is None:
            print("No1 の地震情報が見つかりませんでした。")
            return

        # 必要な情報を取得（存在しない場合は"不明"を設定）
        time = latest.get("time", "不明")
        location = latest.get("location", "不明")
        magnitude = latest.get("magnitude", "不明")
        shindo = latest.get("shindo", "不明")
        depth = latest.get("depth", "不明")
        latitude = latest.get("latitude", "不明")
        longitude = latest.get("longitude", "不明")
        info = latest.get("info", "不明")

        # 時刻を年、月、日、時、分の形式に整形
        if time != "不明":
            try:
                year, month, day_time = time.split("/")
                day, hour_minute = day_time.split(" ")
                hour, minute = hour_minute.split(":")
                # 数字の先頭の0を削除
                year = year.lstrip("0")
                month = month.lstrip("0")
                day = day.lstrip("0")
                hour = hour.lstrip("0")
                minute = minute.lstrip("0")
                formatted_time = f"{hour}時{minute}分"
            except ValueError:
                formatted_time = time  # フォーマットが異なる場合はそのまま使用
        else:
            formatted_time = "不明"

        # 必要な情報を表示
        message = (f"地震情報。{formatted_time}頃、地震がありました。震源地は {location}。"
                   f"震源の深さは {depth}。地震の規模を示すマグニチュードは {magnitude}と推定されています。"
                   f"{info}。"
                   f"この地震により震度{shindo}を観測しました。観測された地点については画面をご覧ください。")
        print("No1 の地震情報:")
        print(f"発生時刻: {time}")
        print(f"震央地名: {location}")
        print(f"マグニチュード: {magnitude}")
        print(f"最大震度: {shindo}")
        print(f"震源の深さ: {depth}")
        print(f"震源の緯度: {latitude}")
        print(f"震源の経度: {longitude}")
        print(f"津波の有無: {info}")

        # 棒読みちゃんで読み上げ
        speak_bouyomi(message)

    except requests.exceptions.RequestException as e:
        print(f"データ取得エラー: {e}")
    except json.JSONDecodeError:
        print("JSONデータの解析に失敗しました。")
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")

def speak_bouyomi(text='ゆっくりしていってね', voice=0, volume=-1, speed=-1, tone=-1):
    try:
        res = requests.get(
            'http://localhost:50080/Talk',
            params={
                'text': text,
                'voice': voice,
                'volume': volume,
                'speed': speed,
                'tone': tone})
        if res.status_code == 200:
            print("棒読みちゃんに送信しました。")
        else:
            print(f"棒読みちゃん送信エラー: ステータスコード {res.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"棒読みちゃんに接続できませんでした: {e}")

if __name__ == "__main__":
    fetch_latest_earthquake()

