# Earthquake-Tsunami-Yomiage
地震情報、津波情報、緊急地震速報の読み上げができるソフトです。

## 設定等について

config.jsonを使って、以下の設定の変更ができます。

・音声ファイルを入れるフォルダの変更

・音声ファイルの名前

・地震時の津波に関するメッセージの変更（「この地震による津波の心配はありません」みたいなやつ）※次のバージョンから

・地震の震度（変える必要はないと思います。）※次のバージョンから

## 音声に関すること

Soundsフォルダには、初期では無音が入っています。

音声を割り当てたい場合のファイル名は

緊急地震速報（警報）→"Eewwarning.mp3"

緊急地震速報（予報）→"Eewforecast.mp3"

津波情報発表→"Tsunami.mp3"

津波情報解除→"Tsunamicancel.mp3"

震度速報→"ScalePrompt.mp3"

震源に関する情報→"Destination.mp3"

震度・震源に関する情報→"Earthquake.mp3"

各地の震度に関する情報→"Earthquake.mp3"

遠地地震情報→"Foreign.mp3"

## 受信できる情報
・震度速報

・震源情報

・震度・震源に関する情報

・各地の震度に関する情報

・遠地地震に関する情報

・その他の情報

・大津波警報、津波警報、津波注意報

・緊急地震速報(予報も警報も)
## 受信したい情報

・今はなし

## 取得先
P2P地震情報 API v2

https://www.p2pquake.net/develop/json_api_v2/#/

Wolfx API

https://wolfx.jp/apidoc
