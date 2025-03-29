# Earthquake-Tsunami-Yomiage
地震情報、津波情報、緊急地震速報の読み上げができるソフトです。

![image](https://github.com/user-attachments/assets/d3edc31e-0721-4869-81eb-fc6fd161f576)

# 設定について

![image](https://github.com/user-attachments/assets/1c7a0fab-36ee-4a88-957d-27e48e41f2ba)

・各音声のONOFF

・棒読みちゃんの声、音量、速度、音程の変更

・棒読みちゃんとのHTTP連携時のポート番号

※ポート番号は棒読みちゃん実行時に、HTTPエラーが発生したときに変更することをお勧めします。また、棒読みちゃん側でも設定の変更が必要です。

![スクリーンショット 2025-03-29 133029](https://github.com/user-attachments/assets/f521693c-3971-4a12-abb4-87664bd9ba51)

上記画像の赤で囲んだ部分→「アプリケーション連携」→「HTTP連携」→「ポート番号」を変更してください。また、「ローカルHTTPサーバー機能を使う」がFalseになっていたらTrueにしてください。設定変更後は棒読みちゃんの再起動が必要です。

## Config.jsonについて

config.jsonを使って、以下の設定の変更ができます。""(ダブルクォーテーション)に囲まれた中のみを変更してください。それ以外を変更すると起動しなくなる可能性があります。

・音声ファイルを入れるフォルダの変更

・音声ファイルの名前

・地震時の津波に関するメッセージの変更（「この地震による津波の心配はありません」みたいなやつ）

・地震情報の名前（「遠地地震情報」みたいなやつ）

・受信先URL（WolfxとP2PのWebsocketになっています）

## 音声に関すること

Soundsフォルダには、初期では無音が入っています。

音声を割り当てたい場合のファイル名は

緊急地震速報（警報）→"Eewwarning.mp3"

緊急地震速報（予報）→"Eewforecast.mp3"

津波情報発表→"Tsunami.mp3"

津波観測に関する情報発表→"Observation.mp3"

津波情報解除→"Tsunamicancel.mp3"

震度速報→"ScalePrompt.mp3"

震源に関する情報→"Destination.mp3"

震度・震源に関する情報→"Earthquake.mp3"

各地の震度に関する情報→"Earthquake.mp3"

遠地地震情報→"Foreign.mp3"

長周期地震動に関する情報→"SeismicWarning.mp3"

## 受信できる情報
・震度速報

・震源情報

・震度・震源に関する情報

・各地の震度に関する情報

・長周期地震動に関する情報

・遠地地震に関する情報

・大津波警報、津波警報、津波注意報

・津波観測に関する情報

## 配信利用について
原則、配信利用時にはクレジット表記は必要ありません。ご自由にお使いください。

ですが、書いてくれると使っていることが分かりやすいので、作者としてはうれしいです。

## 取得先
P2P地震情報 API v2

https://www.p2pquake.net/develop/json_api_v2/#/

Wolfx API

https://wolfx.jp/apidoc
