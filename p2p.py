import requests
from datetime import datetime
import time

# 地震情報を取得する関数
def 地震データ取得():
    url = "https://api.p2pquake.net/v2/history?codes=551&limit=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]  # 最新の地震情報を返す
        else:
            print("地震データがありません。")
    else:
        print(f"データ取得失敗: {response.status_code}")
    return None

# 棒読みちゃんで読み上げる関数
def speak_bouyomi(text='ゆっくりしていってね', voice=0, volume=-1, speed=-1, tone=-1):
    res = requests.get(
        'http://localhost:50080/Talk',
        params={
            'text': text,
            'voice': voice,
            'volume': volume,
            'speed': speed,
            'tone': tone})
    return res.status_code

# 震度の数値を文字列に変換する関数
def 震度変換(scale):
    震度マップ = {
        10: "震度1",
        20: "震度2",
        30: "震度3",
        40: "震度4",
        45: "震度5弱",
        46: "震度5弱以上と推定",
        50: "震度5強",
        55: "震度6弱",
        60: "震度6強",
        70: "震度7"
    }
    return 震度マップ.get(scale, "不明")

# 国内津波情報を変換する関数
def 国内津波変換(tsunami):
    津波マップ = {
        "None": "この地震による津波の心配はありません。",
        "Checking": "津波の有無については現在調査中です。今後の情報に警戒してください。",
        "NonEffective": "この地震により若干の海面変動が予想されますが、津波被害の心配はありません。",
        "Watch": "この地震により、津波注意報が発表されました。",
        "Warning": "この地震により、現在津波情報等を発表中です。"
    }
    return 津波マップ.get(tsunami, "")

# 海外津波情報を変換する関数
def 海外津波変換(tsunami):
    津波マップ = {
        "None": "この地震による津波の心配はありません。",
        "Checking": "この地震による、津波の有無については現在調査中です。今後の情報に警戒してください。",
        "NonEffectiveNearby": "この地震により、震源の近傍では小さな津波が発生するかもしれませんが、被害の心配はありません。",
        "WarningNearby": "この地震により、震源の近傍では津波発生の可能性があります。",
        "WarningPacific": "この地震により、太平洋では津波の発生の可能性があります。",
        "WarningPacificWide": "この地震により、太平洋の広域で津波の可能性があります。",
        "WarningIndian": "この地震により、インド洋では津波の可能性があります。",
        "WarningIndianWide": "この地震により、インド洋の広域で津波の可能性があります。",
        "Potential": "一般にこの規模では津波の可能性があります。"
    }
    return 津波マップ.get(tsunami, "")

# Type情報を変換する関数
def タイプ変換(type_str):
    タイプマップ = {
        "ScalePrompt": "震度速報",
        "Destination": "震源に関する情報",
        "ScaleAndDestination": "地震情報",
        "DetailScale": "地震情報",
        "Foreign": "遠地地震情報",
        "Other": "地震情報"
    }
    return タイプマップ.get(type_str, "地震情報")

# 地震情報を表示して読み上げる関数
def 地震情報表示(data):
    # Type情報
    タイプ = タイプ変換(data.get('issue', {}).get('type', 'Other'))
    読み上げテキスト = f"{タイプ}。"

    # 地震の詳細
    earthquake = data.get('earthquake', {})
    発生日時 = earthquake.get('time', '不明')
    if 発生日時 != '不明':
        dt = datetime.strptime(発生日時, '%Y/%m/%d %H:%M:%S')
        発生日時 = f"{dt.hour}時{dt.minute}分ごろ"

    読み上げテキスト += f"{発生日時}地震がありました。"

    # 震源
    hypocenter = earthquake.get('hypocenter', {})
    震源 = hypocenter.get('name', '不明')
    深さ = hypocenter.get('depth', -1)
    マグニチュード = hypocenter.get('magnitude', -1)

    if 深さ == 0:
        深さ_str = "ごく浅い"
    elif 深さ > 0:
        深さ_str = f"{深さ}キロメートル"
    else:
        深さ_str = None

    if マグニチュード == -1:
        マグニチュード_str = None
    else:
        マグニチュード_str = f"マグニチュードは{マグニチュード:.1f}" if '.' not in str(マグニチュード) else f"マグニチュードは{マグニチュード}"

    if 深さ_str:
        読み上げテキスト += f"震源地は{震源}、震源の深さは{深さ_str}。"
    if マグニチュード_str:
        読み上げテキスト += f"地震の規模を示す{マグニチュード_str}と推定されています。"

    # 津波情報
    issue_type = data.get('issue', {}).get('type', 'Other')
    国内津波 = 国内津波変換(earthquake.get('domesticTsunami', ''))
    if issue_type == "Foreign" and 国内津波 != "この地震による津波の心配はありません。":
        国内津波 = f"、また日本では、{国内津波}"

    if issue_type != "Foreign":
        if 国内津波:
            読み上げテキスト += 国内津波

    海外津波 = 海外津波変換(earthquake.get('foreignTsunami', ''))
    if 海外津波:
        読み上げテキスト += 海外津波

    # 最大震度と観測点（「震源に関する情報」または「遠地地震情報」の場合は省略）
    if issue_type not in ["Destination", "Foreign"]:
        
        # 最大震度と観測点
        最大震度地域 = {}

        for point in data.get('points', []):
            pref = point.get('pref', '不明')
            scale = point.get('scale', -1)

            if scale > 0:  # 有効な震度の場合のみ
                if pref not in 最大震度地域 or scale > 最大震度地域[pref]:
                    最大震度地域[pref] = scale

        # 最大震度とその地域
        最大震度 = max(最大震度地域.values(), default=0)
        最大震度地域リスト = [pref for pref, scale in 最大震度地域.items() if scale == 最大震度]

        # 最大震度未満の震度
        その他震度地域 = {}
        for pref, scale in 最大震度地域.items():
            if scale < 最大震度:
                if scale not in その他震度地域:
                    その他震度地域[scale] = []
                その他震度地域[scale].append(pref)

        # 最大震度のテキスト
        読み上げテキスト += f"最大{震度変換(最大震度)}を{'、 '.join(最大震度地域リスト)}で観測しました。"

        # 最大震度未満のテキスト
        震度一覧 = []
        for scale in sorted(その他震度地域.keys(), reverse=True):
            震度文字列 = 震度変換(scale)
            prefs = '、'.join(その他震度地域[scale])
            震度一覧.append(f"{震度文字列}を{prefs}")

        if 震度一覧:
            読み上げテキスト += "また、" + "、".join(震度一覧) + "で観測しました。"

    print(読み上げテキスト)
    speak_bouyomi(読み上げテキスト)

# メイン処理
def メイン():
    最新データID = None

    # 起動時に一度読み上げ
    初回データ = 地震データ取得()
    if 初回データ:
        最新データID = 初回データ.get('id')
        地震情報表示(初回データ)

    while True:
        data = 地震データ取得()
        if data:
            データID = data.get('id')
            if データID != 最新データID:
                最新データID = データID
                地震情報表示(data)
        time.sleep(2)  # 2秒間隔でデータを取得

if __name__ == "__main__":
    メイン()
