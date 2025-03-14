# CDJ350 Battler

CDJ350で日本語ファイル名のトラックを扱うためのツール。Rekordboxデータベースからプレイリスト情報を読み取り、日本語ファイル名をローマ字に変換してUSBメモリにエクスポートします。

## 主な機能

- Rekordboxのデータベース読み取り
- 日本語ファイル名のローマ字変換
- USB出力形式に合わせたファイル構造の生成
- CDJ350で扱いやすいファイル名の自動生成

## 必要条件

- Python 3.8以上
- pyrekordbox
- pykakasi（日本語のローマ字変換用）

## インストール

```
pip install -r requirements.txt
```

## 使い方

```
python cdj350battler.py --playlist "プレイリスト名" --output /path/to/usb
```

## ライセンス

MIT
