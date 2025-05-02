# EarthquakeTsunamiYomiage

**地震情報・津波情報・緊急地震速報を自動で読み上げるソフトウェアです。**

![トップ画面](https://github.com/user-attachments/assets/d3edc31e-0721-4869-81eb-fc6fd161f576)

---

## 🔧 主な機能

| 機能画面 | 説明 |
|---|---|
| ![トップ画面](https://github.com/user-attachments/assets/d3edc31e-0721-4869-81eb-fc6fd161f576) | 緊急地震速報・津波情報などを一括表示。 |
| ![音声設定](https://github.com/user-attachments/assets/eebba772-fe8e-4524-a30c-65114de39574) | 音声ごとのON/OFF、棒読みちゃんの声・音量・速度・音程の変更が可能。<br>HTTP連携用のポート番号も設定可能。 |
| ![棒読みちゃん設定](https://github.com/user-attachments/assets/f521693c-3971-4a12-abb4-87664bd9ba51) | 棒読みちゃんとの連携設定画面。ポート番号の変更、ローカルHTTPサーバー機能の有効化が可能。 |

---

## ⚙️ 設定について

### 棒読みちゃん連携設定

1. 棒読みちゃんの「アプリケーション連携」→「HTTP連携」→「ポート番号」を変更  
2. 「ローカルHTTPサーバー機能を使う」が `False` になっていたら `True` に変更  
3. 設定後は **棒読みちゃんを再起動** してください  

---

## 🧾 config.jsonについて

`config.json` を編集することで以下の設定が可能です。`""` で囲まれた文字列のみを変更してください。

- 音声ファイルのフォルダパス
- 各種音声ファイル名
- 津波メッセージの文言
- 地震情報のラベル名（例：遠地地震情報）
- WebSocketの受信先URL（P2P/Wolfx）

---

## 🔊 音声ファイルの名前対応表

| 内容 | ファイル名 |
|---|---|
| 緊急地震速報（警報） | `Eewwarning.mp3` |
| 緊急地震速報（予報） | `Eewforecast.mp3` |
| 津波情報発表 | `Tsunami.mp3` |
| 津波観測に関する情報発表 | `Observation.mp3` |
| 津波情報解除 | `Tsunamicancel.mp3` |
| 震度速報 | `ScalePrompt.mp3` |
| 震源に関する情報 | `Destination.mp3` |
| 震度・震源に関する情報 | `ScaleAndDestination.mp3` |
| 各地の震度に関する情報 | `DetailScale.mp3` |
| 遠地地震情報 | `Foreign.mp3` |
| 長周期地震動に関する情報 | `SeismicWarning.mp3` |

> ※ `Sounds` フォルダには初期状態では無音ファイルが入っています。必要に応じて音声ファイルを差し替えてください。

---

## 📡 受信できる情報一覧

- 緊急地震速報（予報・警報）
- 震度速報
- 震源情報
- 震度・震源に関する情報
- 各地の震度に関する情報
- 長周期地震動に関する情報
- 遠地地震に関する情報
- 津波警報／注意報／大津波警報
- 津波観測情報
- 津波情報の解除

---

## 📢 配信での利用について

- クレジット表記は **不要** です。ご自由にご利用ください。
- ただし、書いていただけると使用状況が分かって作者が嬉しく思います。

---

## 🔗 データ取得元

- [P2P地震情報 API v2](https://www.p2pquake.net/develop/json_api_v2/#/)
- [Wolfx API](https://wolfx.jp/apidoc)

---

## 💬 不具合・要望

Issue または Pull Request にてご報告ください。
