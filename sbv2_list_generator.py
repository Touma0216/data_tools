#!/usr/bin/env python3
"""
Style-Bert-VITS2 リストファイル生成ツール
metadata.jsonからesd.list, train.list, val.listを自動生成
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import random
from datetime import datetime
import shutil

class SBV2ListGenerator:
    """Style-Bert-VITS2用のリストファイル生成クラス"""
    
    def __init__(self, model_name: str = "reineHonoka"):
        self.model_name = model_name
        self.metadata = {}
        self.file_list = []
        
    def load_metadata(self, metadata_path: Path) -> bool:
        """metadata.jsonを読み込む"""
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            print(f"✅ メタデータを読み込みました: {len(self.metadata)}個のファイル")
            return True
        except Exception as e:
            print(f"❌ メタデータの読み込みに失敗: {e}")
            return False
    
    def validate_metadata(self) -> List[str]:
        """メタデータの検証"""
        errors = []
        required_fields = ['text', 'speaker', 'language']
        
        for filename, data in self.metadata.items():
            # 必須フィールドのチェック
            for field in required_fields:
                if field not in data:
                    errors.append(f"{filename}: '{field}'フィールドが不足")
            
            # ファイル拡張子チェック
            if not filename.endswith(('.wav', '.mp3', '.flac', '.ogg')):
                errors.append(f"{filename}: サポートされていない音声形式")
        
        if errors:
            print("⚠️ メタデータに問題があります:")
            for error in errors[:10]:  # 最初の10個まで表示
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... 他 {len(errors) - 10} 個のエラー")
        
        return errors
    
    def generate_esd_list(self, output_dir: Path) -> bool:
        """esd.listを生成"""
        esd_lines = []
        
        for filename, data in sorted(self.metadata.items()):
            # 基本情報の取得
            speaker = data.get('speaker', self.model_name)
            language = data.get('language', 'JP')
            text = data.get('text', '')
            
            # テキストの正規化（改行やタブを除去）
            text = text.replace('\n', ' ').replace('\t', ' ').strip()
            
            # esd.list形式: ファイルパス|話者名|言語|テキスト
            line = f"{filename}|{speaker}|{language}|{text}"
            esd_lines.append(line)
        
        # ファイルに書き込み
        esd_path = output_dir / 'esd.list'
        try:
            with open(esd_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(esd_lines))
            print(f"✅ esd.listを生成しました: {len(esd_lines)}行")
            return True
        except Exception as e:
            print(f"❌ esd.list生成エラー: {e}")
            return False
    
    def split_train_val(self, val_ratio: float = 0.1) -> Tuple[List[str], List[str]]:
        """データを学習用と検証用に分割"""
        all_files = list(self.metadata.keys())
        
        # 感情ごとにグループ化（バランスを保つため）
        emotion_groups = {}
        for filename in all_files:
            emotion = self.metadata[filename].get('emotion', 'neutral')
            if emotion not in emotion_groups:
                emotion_groups[emotion] = []
            emotion_groups[emotion].append(filename)
        
        train_files = []
        val_files = []
        
        # 各感情グループから比率に応じて分割
        for emotion, files in emotion_groups.items():
            random.shuffle(files)
            val_count = max(1, int(len(files) * val_ratio))
            val_files.extend(files[:val_count])
            train_files.extend(files[val_count:])
        
        # シャッフル
        random.shuffle(train_files)
        random.shuffle(val_files)
        
        print(f"📊 データ分割: 学習用 {len(train_files)}個 / 検証用 {len(val_files)}個")
        
        # 感情分布を表示
        print("\n感情分布:")
        for emotion in emotion_groups.keys():
            train_emotion = sum(1 for f in train_files if self.metadata[f].get('emotion', 'neutral') == emotion)
            val_emotion = sum(1 for f in val_files if self.metadata[f].get('emotion', 'neutral') == emotion)
            print(f"  {emotion}: 学習用 {train_emotion}個 / 検証用 {val_emotion}個")
        
        return train_files, val_files
    
    def generate_train_val_lists(self, output_dir: Path, val_ratio: float = 0.1) -> bool:
        """train.listとval.listを生成"""
        train_files, val_files = self.split_train_val(val_ratio)
        
        # train.list生成
        train_lines = []
        for filename in train_files:
            data = self.metadata[filename]
            speaker = data.get('speaker', self.model_name)
            language = data.get('language', 'JP')
            text = data.get('text', '').replace('\n', ' ').replace('\t', ' ').strip()
            
            # 注: 音素列は前処理時に自動生成されるため、ここでは基本形式のみ
            line = f"wavs/{filename}|{speaker}|{language}|{text}"
            train_lines.append(line)
        
        # val.list生成
        val_lines = []
        for filename in val_files:
            data = self.metadata[filename]
            speaker = data.get('speaker', self.model_name)
            language = data.get('language', 'JP')
            text = data.get('text', '').replace('\n', ' ').replace('\t', ' ').strip()
            
            line = f"wavs/{filename}|{speaker}|{language}|{text}"
            val_lines.append(line)
        
        # ファイルに書き込み
        try:
            train_path = output_dir / 'train.list'
            with open(train_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(train_lines))
            print(f"✅ train.listを生成しました: {len(train_lines)}行")
            
            val_path = output_dir / 'val.list'
            with open(val_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(val_lines))
            print(f"✅ val.listを生成しました: {len(val_lines)}行")
            
            return True
        except Exception as e:
            print(f"❌ train/val.list生成エラー: {e}")
            return False
    
    def generate_extended_list(self, output_dir: Path) -> bool:
        """拡張情報を含むリストファイルを生成（オプション）"""
        extended_lines = []
        
        for filename, data in sorted(self.metadata.items()):
            # 全フィールドを取得
            speaker = data.get('speaker', self.model_name)
            language = data.get('language', 'JP')
            text = data.get('text', '').replace('\n', ' ').replace('\t', ' ').strip()
            emotion = data.get('emotion', 'neutral')
            emotion_strength = data.get('emotion_strength', 1.0)
            style = data.get('style', 'default')
            speaker_note = data.get('speaker_note', '')
            situation_context = data.get('situation_context', '')
            
            # 拡張形式
            line = f"{filename}|{speaker}|{language}|{text}|{emotion}|{emotion_strength}|{style}|{speaker_note}|{situation_context}"
            extended_lines.append(line)
        
        # ファイルに書き込み
        extended_path = output_dir / 'esd_extended.list'
        try:
            with open(extended_path, 'w', encoding='utf-8') as f:
                # ヘッダー行を追加
                header = "# filename|speaker|language|text|emotion|emotion_strength|style|speaker_note|situation_context"
                f.write(header + '\n')
                f.write('\n'.join(extended_lines))
            print(f"✅ esd_extended.listを生成しました: {len(extended_lines)}行")
            return True
        except Exception as e:
            print(f"❌ extended.list生成エラー: {e}")
            return False
    
    def generate_style_config(self, output_dir: Path) -> bool:
        """スタイル設定ファイルを生成"""
        # 感情とスタイルの統計を収集
        emotions = {}
        styles = {}
        
        for data in self.metadata.values():
            emotion = data.get('emotion', 'neutral')
            style = data.get('style', 'default')
            
            emotions[emotion] = emotions.get(emotion, 0) + 1
            styles[style] = styles.get(style, 0) + 1
        
        style_config = {
            "model_name": self.model_name,
            "emotions": emotions,
            "styles": styles,
            "total_files": len(self.metadata),
            "generated_at": datetime.now().isoformat()
        }
        
        # ファイルに書き込み
        config_path = output_dir / 'style_config.json'
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(style_config, f, ensure_ascii=False, indent=2)
            print(f"✅ style_config.jsonを生成しました")
            return True
        except Exception as e:
            print(f"❌ style_config.json生成エラー: {e}")
            return False
    
    def backup_existing_lists(self, output_dir: Path):
        """既存のリストファイルをバックアップ"""
        backup_dir = output_dir / 'backup' / datetime.now().strftime('%Y%m%d_%H%M%S')
        
        list_files = ['esd.list', 'train.list', 'val.list', 'esd_extended.list']
        files_to_backup = []
        
        for file in list_files:
            file_path = output_dir / file
            if file_path.exists():
                files_to_backup.append(file_path)
        
        if files_to_backup:
            backup_dir.mkdir(parents=True, exist_ok=True)
            for file_path in files_to_backup:
                shutil.copy2(file_path, backup_dir / file_path.name)
            print(f"📁 既存ファイルをバックアップしました: {backup_dir}")


def main():
    """メイン関数"""
    print("\n=== Style-Bert-VITS2 リストファイル生成ツール ===")
    print("metadata.jsonから各種リストファイルを生成します\n")
    
    # 設定
    model_name = input("モデル名を入力 (default: reineHonoka): ").strip() or "reineHonoka"
    
    # パスの設定
    base_dir = Path(f"Data/{model_name}")
    metadata_path = base_dir / "metadata.json"
    
    # メタデータの存在確認
    if not metadata_path.exists():
        print(f"❌ metadata.jsonが見つかりません: {metadata_path}")
        
        # サンプルmetadata.jsonを生成
        print("\nサンプルのmetadata.jsonを生成しますか？ (y/n): ", end="")
        if input().lower() == 'y':
            create_sample_metadata(base_dir)
            print(f"📝 サンプルを生成しました: {metadata_path}")
            print("編集してから再度実行してください")
        return
    
    # ジェネレーター初期化
    generator = SBV2ListGenerator(model_name)
    
    # メタデータ読み込み
    if not generator.load_metadata(metadata_path):
        return
    
    # 検証
    errors = generator.validate_metadata()
    if errors:
        print("\n続行しますか？ (y/n): ", end="")
        if input().lower() != 'y':
            return
    
    # 既存ファイルのバックアップ
    generator.backup_existing_lists(base_dir)
    
    # 検証用データの比率
    val_ratio_str = input("\n検証用データの比率 (default: 0.1): ").strip()
    val_ratio = float(val_ratio_str) if val_ratio_str else 0.1
    
    # リストファイル生成
    print("\n📝 リストファイルを生成中...")
    
    # esd.list
    generator.generate_esd_list(base_dir)
    
    # train.list / val.list
    generator.generate_train_val_lists(base_dir, val_ratio)
    
    # 拡張リスト（オプション）
    print("\n拡張リストファイルも生成しますか？ (y/n): ", end="")
    if input().lower() == 'y':
        generator.generate_extended_list(base_dir)
    
    # スタイル設定
    generator.generate_style_config(base_dir)
    
    print("\n✨ 完了！")
    print(f"生成されたファイルは {base_dir} にあります")


def create_sample_metadata(base_dir: Path):
    """サンプルのmetadata.jsonを作成"""
    base_dir.mkdir(parents=True, exist_ok=True)
    
    sample_metadata = {
        "001.wav": {
            "text": "こんにちは、零音ほのかです",
            "speaker": "reineHonoka",
            "language": "JP",
            "emotion": "happy",
            "emotion_strength": 0.8,
            "style": "cheerful",
            "speaker_note": "<Parse_happy>明るく元気な挨拶",
            "situation_context": "配信開始の挨拶"
        },
        "002.wav": {
            "text": "今日も一緒に頑張りましょう",
            "speaker": "reineHonoka",
            "language": "JP",
            "emotion": "happy",
            "emotion_strength": 0.7,
            "style": "encouraging",
            "speaker_note": "<Parse_happy>励ましのトーン",
            "situation_context": "リスナーへの応援"
        },
        "003.wav": {
            "text": "どうしてこんなことに...",
            "speaker": "reineHonoka",
            "language": "JP",
            "emotion": "sad",
            "emotion_strength": 0.9,
            "style": "depressed",
            "speaker_note": "<Parse_sad>深い悲しみを込めて",
            "situation_context": "ゲームで大失敗した時"
        },
        "004.wav": {
            "text": "ちょっと、それはないでしょ！",
            "speaker": "reineHonoka",
            "language": "JP",
            "emotion": "angry",
            "emotion_strength": 0.6,
            "style": "frustrated",
            "speaker_note": "<Parse_angry>軽い怒りと呆れ",
            "situation_context": "理不尽な展開への反応"
        },
        "005.wav": {
            "text": "えっと...その...なんというか...",
            "speaker": "reineHonoka",
            "language": "JP",
            "emotion": "embarrassed",
            "emotion_strength": 0.8,
            "style": "shy",
            "speaker_note": "<Parse_embarrassed>恥ずかしそうに",
            "situation_context": "褒められた時の反応"
        },
        "006.wav": {
            "text": "本当に怖いんだって！",
            "speaker": "reineHonoka",
            "language": "JP",
            "emotion": "fear",
            "emotion_strength": 0.95,
            "style": "terrified",
            "speaker_note": "<Parse_fear>震え声で",
            "situation_context": "ホラーゲーム実況中"
        },
        "007.wav": {
            "text": "やったー！ついに成功した！",
            "speaker": "reineHonoka",
            "language": "JP",
            "emotion": "happy",
            "emotion_strength": 1.0,
            "style": "excited",
            "speaker_note": "<Parse_happy>大喜びで叫ぶ",
            "situation_context": "難しいミッションクリア"
        },
        "008.wav": {
            "text": "みんな、本当にありがとう",
            "speaker": "reineHonoka",
            "language": "JP",
            "emotion": "grateful",
            "emotion_strength": 0.85,
            "style": "heartfelt",
            "speaker_note": "<Parse_grateful>心を込めて",
            "situation_context": "配信終了時の感謝"
        }
    }
    
    metadata_path = base_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(sample_metadata, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()