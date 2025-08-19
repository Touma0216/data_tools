#!/usr/bin/env python3
"""
音声ファイル変換ツール
Style-Bert-VITS2の学習データ準備用
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# ========================================
# ファイルパス設定（ここを編集してください）
# ========================================
INPUT_PATH = "jvs_data/VOICEACTRESS100_001.wav"  # 変換したいファイル/フォルダのパス
OUTPUT_DIR = None     # 出力ディレクトリ (Noneで同じ場所に保存)ti
# ========================================

try:
    from pydub import AudioSegment
    from pydub.utils import make_chunks
    import librosa
    import soundfile as sf
    from tqdm import tqdm
except ImportError as e:
    print(f"必要なライブラリがインストールされていません: {e}")
    print("\n以下のコマンドでインストールしてください:")
    print("pip install pydub librosa soundfile tqdm")
    sys.exit(1)

# ffmpegの確認
try:
    AudioSegment.converter = "ffmpeg"
    AudioSegment.silent(duration=1)
except:
    print("Error: ffmpegがインストールされていません")
    print("ffmpegをインストールしてください: https://ffmpeg.org/download.html")
    sys.exit(1)


class AudioConverter:
    """音声ファイル変換クラス"""
    
    SUPPORTED_FORMATS = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac']
    SAMPLE_RATES = [8000, 16000, 22050, 44100, 48000]
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.error_files = []
    
    def get_audio_files(self, path: Path, extensions: List[str]) -> List[Path]:
        """指定パスから音声ファイルを取得"""
        audio_files = []
        
        if path.is_file():
            if any(path.suffix.lower() == f'.{ext}' for ext in extensions):
                audio_files.append(path)
        elif path.is_dir():
            for ext in extensions:
                audio_files.extend(path.glob(f'**/*.{ext}'))
                audio_files.extend(path.glob(f'**/*.{ext.upper()}'))
        
        return sorted(set(audio_files))
    
    def convert_format(self, input_file: Path, output_format: str, output_dir: Optional[Path] = None) -> bool:
        """音声形式を変換"""
        try:
            # 出力パスの設定
            if output_dir:
                output_file = output_dir / f"{input_file.stem}.{output_format}"
            else:
                output_file = input_file.parent / f"{input_file.stem}_converted.{output_format}"
            
            # 音声読み込み
            audio = AudioSegment.from_file(str(input_file))
            
            # 形式変換して保存
            audio.export(str(output_file), format=output_format)
            
            return True
        except Exception as e:
            print(f"  エラー: {input_file.name} - {str(e)}")
            self.error_files.append(str(input_file))
            return False
    
    def convert_audio_properties(self, 
                                input_file: Path,
                                sample_rate: Optional[int] = None,
                                channels: Optional[int] = None,
                                bit_depth: Optional[int] = None,
                                output_dir: Optional[Path] = None) -> bool:
        """音声プロパティを変換（サンプルレート、チャンネル数、ビット深度）"""
        try:
            # librosaで読み込み（元のサンプルレートを保持）
            audio_data, orig_sr = librosa.load(str(input_file), sr=None, mono=False)
            
            # モノラル/ステレオ変換
            if channels == 1 and len(audio_data.shape) > 1:
                audio_data = librosa.to_mono(audio_data)
            elif channels == 2 and len(audio_data.shape) == 1:
                audio_data = np.stack([audio_data, audio_data])
            
            # サンプルレート変換
            if sample_rate and sample_rate != orig_sr:
                if len(audio_data.shape) > 1:
                    # ステレオの場合
                    audio_data = np.array([librosa.resample(audio_data[i], orig_sr=orig_sr, target_sr=sample_rate) 
                                         for i in range(audio_data.shape[0])])
                else:
                    # モノラルの場合
                    audio_data = librosa.resample(audio_data, orig_sr=orig_sr, target_sr=sample_rate)
            else:
                sample_rate = orig_sr
            
            # 転置（soundfileの形式に合わせる）
            if len(audio_data.shape) > 1:
                audio_data = audio_data.T
            
            # 出力パスの設定
            if output_dir:
                output_file = output_dir / input_file.name
            else:
                suffix_parts = []
                if sample_rate: suffix_parts.append(f"{sample_rate}Hz")
                if channels: suffix_parts.append(f"{channels}ch")
                if bit_depth: suffix_parts.append(f"{bit_depth}bit")
                suffix = "_" + "_".join(suffix_parts) if suffix_parts else "_converted"
                output_file = input_file.parent / f"{input_file.stem}{suffix}{input_file.suffix}"
            
            # ビット深度の設定
            subtype = 'PCM_16' if bit_depth == 16 else 'PCM_24' if bit_depth == 24 else 'PCM_32'
            
            # 保存
            sf.write(str(output_file), audio_data, sample_rate, subtype=subtype)
            
            return True
        except Exception as e:
            print(f"  エラー: {input_file.name} - {str(e)}")
            self.error_files.append(str(input_file))
            return False
    
    def process_files(self, files: List[Path], operation: str, **kwargs):
        """ファイルを一括処理"""
        print(f"\n{len(files)}個のファイルを処理します...")
        
        with tqdm(total=len(files), desc="変換中") as pbar:
            for file in files:
                success = False
                
                if operation == 'format':
                    success = self.convert_format(file, **kwargs)
                elif operation == 'properties':
                    success = self.convert_audio_properties(file, **kwargs)
                
                if success:
                    self.processed_count += 1
                else:
                    self.error_count += 1
                
                pbar.update(1)
                pbar.set_postfix({
                    '成功': self.processed_count,
                    'エラー': self.error_count
                })


def main():
    """メイン関数"""
    converter = AudioConverter()
    
    print("\n=== 音声ファイル変換ツール ===")
    print("Style-Bert-VITS2 学習データ準備用\n")
    
    # 設定されたパスの確認
    path = Path(INPUT_PATH)
    
    if not path.exists():
        print(f"エラー: 設定されたパス '{INPUT_PATH}' が見つかりません。")
        print("スクリプト内の INPUT_PATH を正しいパスに変更してください。")
        sys.exit(1)
    
    print(f"入力パス: {path}")
    
    # 出力ディレクトリの設定
    output_dir = Path(OUTPUT_DIR) if OUTPUT_DIR else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"出力先: {output_dir}")
    else:
        print("出力先: 元ファイルと同じ場所")
    
    # 変換モードの選択
    print("\n変換モードを選択してください:")
    print("1. 形式変換 (wav → mp3, mp3 → wav など)")
    print("2. 音声プロパティ変換 (サンプルレート、チャンネル、ビット深度)")
    
    while True:
        mode = input("\n選択 (1 or 2): ").strip()
        if mode in ['1', '2']:
            break
        print("1 または 2 を入力してください。")
    
    if mode == '1':
        # 形式変換モード
        print("\n現在の音声形式を選択してください:")
        formats = AudioConverter.SUPPORTED_FORMATS
        for i, fmt in enumerate(formats, 1):
            print(f"{i}. {fmt}")
        
        while True:
            try:
                input_fmt_idx = int(input("選択: ")) - 1
                if 0 <= input_fmt_idx < len(formats):
                    input_format = formats[input_fmt_idx]
                    break
            except ValueError:
                pass
            print("正しい番号を入力してください。")
        
        print("\n変換先の形式を選択してください:")
        for i, fmt in enumerate(formats, 1):
            if fmt != input_format:
                print(f"{i}. {fmt}")
        
        while True:
            try:
                output_fmt_idx = int(input("選択: ")) - 1
                if 0 <= output_fmt_idx < len(formats) and formats[output_fmt_idx] != input_format:
                    output_format = formats[output_fmt_idx]
                    break
            except ValueError:
                pass
            print("正しい番号を入力してください。")
        
        # ファイル取得と変換
        files = converter.get_audio_files(path, [input_format])
        if not files:
            print(f"\n{input_format}ファイルが見つかりません。")
            return
        
        print(f"\n{len(files)}個の{input_format}ファイルを{output_format}に変換します。")
        confirm = input("続行しますか？ (y/n): ").lower()
        
        if confirm == 'y':
            converter.process_files(files, 'format', 
                                  output_format=output_format, 
                                  output_dir=output_dir)
    
    else:
        # 音声プロパティ変換モード
        print("\n変換したいファイルの形式を選択してください:")
        formats = AudioConverter.SUPPORTED_FORMATS
        for i, fmt in enumerate(formats, 1):
            print(f"{i}. {fmt}")
        
        while True:
            try:
                fmt_idx = int(input("選択: ")) - 1
                if 0 <= fmt_idx < len(formats):
                    target_format = formats[fmt_idx]
                    break
            except ValueError:
                pass
            print("正しい番号を入力してください。")
        
        # サンプルレート設定
        print("\nサンプルレートを変更しますか？")
        print("1. 8000 Hz")
        print("2. 16000 Hz")
        print("3. 22050 Hz")
        print("4. 44100 Hz")
        print("5. 48000 Hz")
        print("0. 変更しない")
        
        sample_rate = None
        while True:
            try:
                sr_choice = int(input("選択: "))
                if sr_choice == 0:
                    break
                elif 1 <= sr_choice <= 5:
                    sample_rate = AudioConverter.SAMPLE_RATES[sr_choice - 1]
                    break
            except ValueError:
                pass
            print("正しい番号を入力してください。")
        
        # チャンネル設定
        print("\nチャンネル数を変更しますか？")
        print("1. モノラル (1ch)")
        print("2. ステレオ (2ch)")
        print("0. 変更しない")
        
        channels = None
        while True:
            try:
                ch_choice = int(input("選択: "))
                if ch_choice == 0:
                    break
                elif ch_choice in [1, 2]:
                    channels = ch_choice
                    break
            except ValueError:
                pass
            print("正しい番号を入力してください。")
        
        # ビット深度設定
        print("\nビット深度を変更しますか？")
        print("1. 16 bit")
        print("2. 24 bit")
        print("3. 32 bit")
        print("0. 変更しない")
        
        bit_depth = None
        while True:
            try:
                bit_choice = int(input("選択: "))
                if bit_choice == 0:
                    break
                elif bit_choice == 1:
                    bit_depth = 16
                    break
                elif bit_choice == 2:
                    bit_depth = 24
                    break
                elif bit_choice == 3:
                    bit_depth = 32
                    break
            except ValueError:
                pass
            print("正しい番号を入力してください。")
        
        # ファイル取得と変換
        files = converter.get_audio_files(path, [target_format])
        if not files:
            print(f"\n{target_format}ファイルが見つかりません。")
            return
        
        print(f"\n{len(files)}個の{target_format}ファイルを変換します。")
        settings = []
        if sample_rate: settings.append(f"サンプルレート: {sample_rate}Hz")
        if channels: settings.append(f"チャンネル: {channels}ch")
        if bit_depth: settings.append(f"ビット深度: {bit_depth}bit")
        
        if settings:
            print("変換設定:", " / ".join(settings))
            confirm = input("続行しますか？ (y/n): ").lower()
            
            if confirm == 'y':
                converter.process_files(files, 'properties',
                                      sample_rate=sample_rate,
                                      channels=channels,
                                      bit_depth=bit_depth,
                                      output_dir=output_dir)
        else:
            print("変換する設定が選択されていません。")
            return
    
    # 結果表示
    print(f"\n=== 変換完了 ===")
    print(f"成功: {converter.processed_count}個")
    print(f"エラー: {converter.error_count}個")
    
    if converter.error_files:
        print("\nエラーが発生したファイル:")
        for file in converter.error_files[:10]:  # 最初の10個まで表示
            print(f"  - {file}")
        if len(converter.error_files) > 10:
            print(f"  ... 他 {len(converter.error_files) - 10} 個")


if __name__ == "__main__":
    try:
        import numpy as np
    except ImportError:
        print("numpyがインストールされていません。")
        print("pip install numpy")
        sys.exit(1)
    
    main()