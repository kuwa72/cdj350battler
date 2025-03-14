#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CDJ350 Battler - Rekordboxデータベースからプレイリストを読み取り、
日本語ファイル名をローマ字に変換してUSBメモリにエクスポートするツール。
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import pykakasi
from tqdm import tqdm

try:
    from pyrekordbox.db6 import Rekordbox6Database, DbTrack, DbPlaylist
except ImportError:
    print("pyrekordboxがインストールされていません。")
    print("pip install pyrekordbox でインストールしてください。")
    sys.exit(1)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cdj350battler")

class Cdj350Battler:
    """CDJ350用のUSBエクスポートを行うメインクラス"""

    def __init__(self, output_dir: str, debug: bool = False):
        """
        初期化

        Args:
            output_dir: 出力先ディレクトリ
            debug: デバッグモード
        """
        self.output_dir = Path(output_dir)
        self.rekordbox_db = None
        self.kakasi = pykakasi.kakasi()
        
        if debug:
            logger.setLevel(logging.DEBUG)

    def connect_to_rekordbox(self) -> None:
        """Rekordboxデータベースに接続"""
        try:
            self.rekordbox_db = Rekordbox6Database()
            logger.info(f"Rekordboxデータベースに接続しました")
        except Exception as e:
            logger.error(f"Rekordboxデータベースへの接続に失敗しました: {e}")
            sys.exit(1)

    def get_playlists(self) -> List[DbPlaylist]:
        """プレイリスト一覧を取得"""
        playlists = self.rekordbox_db.get_playlists()
        return playlists
    
    def get_playlist_by_name(self, name: str) -> Optional[DbPlaylist]:
        """名前でプレイリストを検索"""
        playlists = self.get_playlists()
        for playlist in playlists:
            if playlist.name == name:
                return playlist
        return None
    
    def to_romaji(self, text: str) -> str:
        """日本語テキストをローマ字に変換"""
        result = self.kakasi.convert(text)
        romaji = "".join([item['hepburn'] for item in result])
        # 空白をアンダースコアに置換
        romaji = romaji.replace(" ", "_")
        # ファイル名に使えない文字を置換
        romaji = "".join(c if c.isalnum() or c in '_-.' else '_' for c in romaji)
        return romaji
    
    def prepare_output_directory(self) -> None:
        """出力ディレクトリの準備"""
        # USBエクスポート用のディレクトリ構造を作成
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)
        
        # CDJ用のディレクトリ構造を作成
        pioneer_dir = self.output_dir / "PIONEER"
        if not pioneer_dir.exists():
            pioneer_dir.mkdir()
        
        # コンテンツディレクトリ
        contents_dir = pioneer_dir / "CONTENTS"
        if not contents_dir.exists():
            contents_dir.mkdir()
            
        # 音楽ファイル用ディレクトリ
        music_dir = self.output_dir / "MUSIC"
        if not music_dir.exists():
            music_dir.mkdir()

    def export_playlist(self, playlist_name: str) -> None:
        """
        指定したプレイリストをエクスポート

        Args:
            playlist_name: エクスポートするプレイリスト名
        """
        self.connect_to_rekordbox()
        self.prepare_output_directory()
        
        # プレイリストを検索
        playlist = self.get_playlist_by_name(playlist_name)
        if not playlist:
            logger.error(f"プレイリスト '{playlist_name}' が見つかりません")
            return
        
        logger.info(f"プレイリスト '{playlist_name}' をエクスポートします")
        
        # プレイリスト内のトラックを取得
        track_ids = self.rekordbox_db.get_playlist_entries(playlist.id)
        tracks = [self.rekordbox_db.get_track(track_id) for track_id in track_ids]
        
        # トラックをエクスポート
        music_dir = self.output_dir / "MUSIC"
        
        for i, track in enumerate(tqdm(tracks, desc="トラックのエクスポート")):
            # 元のパスからファイルを取得
            src_path = Path(track.file_path)
            if not src_path.exists():
                logger.warning(f"ファイルが見つかりません: {src_path}")
                continue
                
            # ファイル名を変換
            orig_filename = src_path.stem
            romaji_filename = self.to_romaji(orig_filename)
            
            # トラック番号を追加して並び順を保持
            padded_num = str(i+1).zfill(3)
            new_filename = f"{padded_num}_{romaji_filename}{src_path.suffix}"
            
            # コピー先パス
            dst_path = music_dir / new_filename
            
            # ファイルをコピー
            try:
                shutil.copy2(src_path, dst_path)
                logger.debug(f"コピー: {src_path} -> {dst_path}")
            except Exception as e:
                logger.error(f"ファイルコピーに失敗しました: {e}")
        
        # プレイリストエクスポート情報をログに出力
        logger.info(f"エクスポート完了: {len(tracks)}トラック")

    def list_playlists(self) -> None:
        """利用可能なプレイリスト一覧を表示"""
        self.connect_to_rekordbox()
        playlists = self.get_playlists()
        
        print("\n利用可能なプレイリスト:")
        print("=" * 60)
        for i, playlist in enumerate(playlists, 1):
            print(f"{i:3d}. {playlist.name}")
        print("=" * 60)


@click.group()
def cli():
    """CDJ350 Battler - CDJ350で日本語ファイル名を扱うためのツール"""
    pass


@cli.command()
@click.option('--playlist', '-p', required=True, help='エクスポートするプレイリスト名')
@click.option('--output', '-o', required=True, help='エクスポート先のUSBディレクトリ')
@click.option('--debug', '-d', is_flag=True, help='デバッグ情報を表示')
def export(playlist: str, output: str, debug: bool):
    """指定したプレイリストをUSBにエクスポート"""
    battler = Cdj350Battler(output, debug)
    battler.export_playlist(playlist)


@cli.command()
def list_playlists():
    """利用可能なプレイリスト一覧を表示"""
    battler = Cdj350Battler("", debug=False)
    battler.list_playlists()


if __name__ == "__main__":
    cli()
