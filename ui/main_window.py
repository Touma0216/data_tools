import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction

# 自作モジュール
# 注: ここは相対パスでインポートするように修正する必要があるかもしれません
from ui.model_loader import ModelLoaderDialog
from ui.tabbed_emotion_control import TabbedEmotionControl
from ui.multi_text import MultiTextWidget
from core.tts_engine import TTSEngine
from core.model_manager import ModelManager


class TTSStudioMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # TTSエンジン初期化
        self.tts_engine = TTSEngine()
        
        # モデル管理初期化
        self.model_manager = ModelManager()
        
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウ設定
        self.setWindowTitle("TTSスタジオ - ほのかちゃん")
        self.setGeometry(100, 100, 1200, 800)
        
        # メニューバーを作成
        self.create_menu_bar()
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # メインコンテンツエリア
        content_layout = QHBoxLayout()
        
        # 左側: テキスト入力とコントロール
        left_layout = QVBoxLayout()
        
        # 複数テキスト入力エリア
        self.multi_text = MultiTextWidget()
        self.multi_text.play_single_requested.connect(self.play_single_text)
        self.multi_text.row_added.connect(self.on_text_row_added)
        self.multi_text.row_removed.connect(self.on_text_row_removed)
        self.multi_text.row_numbers_updated.connect(self.on_row_numbers_updated)
        
        # パラメータエリア
        params_label = QLabel("音声パラメータ:")
        params_label.setFont(QFont("", 10, QFont.Weight.Bold))
        
        # タブ式感情制御ウィジェット
        self.tabbed_emotion_control = TabbedEmotionControl()
        self.tabbed_emotion_control.parameters_changed.connect(self.on_parameters_changed)
        
        # 初期タブを作成（MultiTextWidgetの初期行 "initial" に対応）
        self.tabbed_emotion_control.add_text_row("initial", 1)
        
        # 制御ボタン（3つ）
        controls_layout = QHBoxLayout()
        controls_layout.addStretch()
        
        # 連続再生ボタン
        self.sequential_play_btn = QPushButton("連続して再生")
        self.sequential_play_btn.setMinimumHeight(40)
        self.sequential_play_btn.setEnabled(False)
        self.sequential_play_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 16px;
            }
            QPushButton:hover:enabled {
                background-color: #f57c00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.sequential_play_btn.clicked.connect(self.play_sequential)
        
        # 個別保存ボタン
        self.save_individual_btn = QPushButton("個別保存")
        self.save_individual_btn.setMinimumHeight(40)
        self.save_individual_btn.setEnabled(False)
        self.save_individual_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 16px;
            }
            QPushButton:hover:enabled {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.save_individual_btn.clicked.connect(self.save_individual)
        
        # 連続保存ボタン
        self.save_continuous_btn = QPushButton("連続保存")
        self.save_continuous_btn.setMinimumHeight(40)
        self.save_continuous_btn.setEnabled(False)
        self.save_continuous_btn.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 16px;
            }
            QPushButton:hover:enabled {
                background-color: #7b1fa2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.save_continuous_btn.clicked.connect(self.save_continuous)
        
        controls_layout.addWidget(self.sequential_play_btn)
        controls_layout.addWidget(self.save_individual_btn)
        controls_layout.addWidget(self.save_continuous_btn)
        
        # 左側レイアウト組み立て
        left_layout.addWidget(self.multi_text, 1)
        left_layout.addWidget(params_label)
        left_layout.addWidget(self.tabbed_emotion_control, 1)
        left_layout.addLayout(controls_layout)
        
        # 右側: Live2D表示エリア
        self.live2d_widget = QWidget()
        self.live2d_widget.setMaximumWidth(300)
        self.live2d_widget.setMinimumWidth(250)
        self.live2d_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        
        live2d_layout = QVBoxLayout(self.live2d_widget)
        live2d_label = QLabel("Live2D\nリップシンクエリア")
        live2d_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        live2d_label.setStyleSheet("color: #666; font-size: 14px; border: none;")
        live2d_layout.addWidget(live2d_label)
        
        # メインコンテンツレイアウト
        content_layout.addLayout(left_layout, 1)
        content_layout.addWidget(self.live2d_widget, 0)
        
        # レイアウトに追加
        main_layout.addLayout(content_layout)

    def create_menu_bar(self):
        """メニューバーを作成"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #f8f9fa;
                color: #333;
                border-bottom: 1px solid #dee2e6;
                padding: 4px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                margin: 0px 2px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #e9ecef;
            }
            QMenuBar::item:pressed {
                background-color: #dee2e6;
            }
            QMenu {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 8px 20px;
                margin: 2px 4px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QMenu::separator {
                height: 1px;
                background-color: #dee2e6;
                margin: 4px 8px;
            }
        """)
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        
        # モデル読み込みアクション
        load_model_action = QAction("📁 モデルを読み込み", self)
        load_model_action.setStatusTip("Style-Bert-VITS2モデルを読み込む")
        load_model_action.triggered.connect(self.open_model_loader)
        file_menu.addAction(load_model_action)
        
        # 区切り線
        file_menu.addSeparator()
        
        # モデル履歴から読み込みアクション
        load_from_history_action = QAction("📋 モデル履歴から読み込み", self)
        load_from_history_action.setStatusTip("過去に読み込んだモデルから選択")
        load_from_history_action.triggered.connect(self.show_model_history_dialog)
        file_menu.addAction(load_from_history_action)
    
    def trim_silence(self, audio, sample_rate, threshold=0.03):
        """音声データの末尾無音を削除"""
        import numpy as np
        
        # 末尾から逆向きに検索して、閾値以上の音がある位置を見つける
        for i in range(len(audio) - 1, -1, -1):
            if abs(audio[i]) > threshold:
                # 0.02秒のバッファを残して切る
                buffer_samples = int(sample_rate * 0.02)
                end_pos = min(i + buffer_samples, len(audio))
                return audio[:end_pos]
        return audio
    
    def on_text_row_added(self, row_id, row_number):
        """テキスト行が追加された時"""
        self.tabbed_emotion_control.add_text_row(row_id, row_number)
    
    def on_text_row_removed(self, row_id):
        """テキスト行が削除された時"""
        self.tabbed_emotion_control.remove_text_row(row_id)
    
    def on_row_numbers_updated(self, row_mapping):
        """行番号が更新された時"""
        self.tabbed_emotion_control.update_tab_numbers(row_mapping)
        
    def open_model_loader(self):
        """モデル読み込みダイアログを開く"""
        dialog = ModelLoaderDialog(self)
        dialog.model_loaded.connect(self.load_model)
        dialog.exec()
        
    def show_model_history_dialog(self):
        """モデル履歴選択ダイアログを表示"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QMessageBox
        
        models = self.model_manager.get_all_models()
        if not models:
            QMessageBox.information(self, "履歴なし", "モデル履歴がありません。")
            return
        
        # ダイアログ作成
        dialog = QDialog(self)
        dialog.setWindowTitle("モデル履歴から選択")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # リストウィジェット
        history_list = QListWidget()
        
        for model_data in models:
            item_text = f"{model_data['name']}\n最終使用: {self.model_manager.get_formatted_datetime(model_data.get('last_used', ''))}\n{model_data['model_path']}"
            
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, model_data)
            
            # ファイル存在チェック
            if not self.model_manager.validate_model_files(model_data):
                list_item.setText(item_text + "\n[ファイルが見つかりません]")
                list_item.setBackground(Qt.GlobalColor.lightGray)
            
            history_list.addItem(list_item)
        
        layout.addWidget(history_list)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(dialog.reject)
        
        load_btn = QPushButton("読み込み")
        load_btn.clicked.connect(lambda: self.load_selected_model(dialog, history_list))
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(load_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def load_selected_model(self, dialog, history_list):
        """選択されたモデルを読み込み"""
        current_item = history_list.currentItem()
        if not current_item:
            return
        
        model_data = current_item.data(Qt.ItemDataRole.UserRole)
        
        # ファイル存在チェック
        if not self.model_manager.validate_model_files(model_data):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(dialog, "エラー", "モデルファイルが見つかりません。")
            return
        
        # モデル読み込み
        paths = {
            'model_path': model_data['model_path'],
            'config_path': model_data['config_path'],
            'style_path': model_data['style_path']
        }
        
        dialog.accept()
        self.load_model(paths)
        
        # 履歴を更新（最終使用日時）
        self.model_manager.update_last_used(model_data['id'])
        
    def load_model(self, paths):
        """モデルを読み込む"""
        success = self.tts_engine.load_model(
            paths['model_path'],
            paths['config_path'], 
            paths['style_path']
        )
        
        if success:
            model_name = Path(paths['model_path']).stem
            print(f"モデル読み込み完了: {model_name}")
            
            # 履歴に追加（新規の場合のみ）
            self.model_manager.add_model(
                paths['model_path'],
                paths['config_path'],
                paths['style_path']
            )
            
            # ボタンを有効化
            self.sequential_play_btn.setEnabled(True)
            self.save_individual_btn.setEnabled(True)
            self.save_continuous_btn.setEnabled(True)
        else:
            print("モデル読み込み失敗")
            # ボタンを無効化
            self.sequential_play_btn.setEnabled(False)
            self.save_individual_btn.setEnabled(False)
            self.save_continuous_btn.setEnabled(False)
    
    def on_parameters_changed(self, row_id, params):
        """感情制御パラメータが変更された時の処理"""
        print(f"行 {row_id} のパラメータ更新: {params}")
    
    def play_single_text(self, row_id, text, parameters):
        """単一テキストを再生（個別パラメータ使用）"""
        if not self.tts_engine.is_loaded:
            print("モデルが読み込まれていません")
            return
        
        # タブ式コントロールから個別パラメータを取得
        tab_parameters = self.tabbed_emotion_control.get_parameters(row_id)
        if tab_parameters:
            parameters = tab_parameters
            print(f"タブパラメータ使用: {tab_parameters}")
        else:
            print(f"デフォルトパラメータ使用: {parameters}")
        
        try:
            print(f"行 {row_id} を再生: {text}")
            
            # 音声合成
            sr, audio = self.tts_engine.synthesize(text, **parameters)
            
            # バックグラウンドで再生
            import sounddevice as sd
            sd.play(audio, sr, blocking=False)
            
        except Exception as e:
            print(f"音声合成エラー: {str(e)}")
    
    def play_sequential(self):
        """連続して再生（1→2→3の順で、各タブのパラメータ使用）"""
        if not self.tts_engine.is_loaded:
            print("モデルが読み込まれていません")
            return
        
        # 全テキストを取得
        texts_data = self.multi_text.get_all_texts_and_parameters()
        if not texts_data:
            print("テキストを入力してください")
            return
        
        try:
            print(f"連続再生開始: {len(texts_data)}件")
            
            # ボタンを一時無効化
            self.sequential_play_btn.setEnabled(False)
            self.sequential_play_btn.setText("再生中...")
            
            # 全ての音声を合成（各行の個別パラメータ使用）
            all_audio = []
            sample_rate = None
            
            for i, data in enumerate(texts_data, 1):
                text = data['text']
                row_id = data['row_id']
                
                # 対応するタブのパラメータを取得
                tab_parameters = self.tabbed_emotion_control.get_parameters(row_id)
                if not tab_parameters:
                    # デフォルトパラメータ
                    tab_parameters = {
                        'style': 'Neutral', 'style_weight': 1.0,
                        'length_scale': 0.85, 'pitch_scale': 1.0,
                        'intonation_scale': 1.0, 'sdp_ratio': 0.25, 'noise': 0.35
                    }
                
                print(f"  {i}. 合成中: {text}")
                
                sr, audio = self.tts_engine.synthesize(text, **tab_parameters)
                
                if sample_rate is None:
                    sample_rate = sr
                
                all_audio.append(audio)
            
            # 音声を結合（末尾無音削除）
            import numpy as np
            
            combined_audio = []
            for i, audio in enumerate(all_audio):
                # 音声データをfloat32に正規化
                if audio.dtype != np.float32:
                    audio = audio.astype(np.float32)
                
                # 音量を制限（クリッピング防止）
                max_val = np.abs(audio).max()
                if max_val > 0.8:
                    audio = audio * (0.8 / max_val)
                
                # 末尾無音を削除
                audio = self.trim_silence(audio, sample_rate)
                print(f"音声 {i+1}: 元の長さ {len(all_audio[i])/sample_rate:.2f}秒 → 無音削除後 {len(audio)/sample_rate:.2f}秒")
                
                combined_audio.append(audio)
            
            final_audio = np.concatenate(combined_audio).astype(np.float32)
            
            # 最終的なクリッピング防止
            max_final = np.abs(final_audio).max()
            if max_final > 0.9:
                final_audio = final_audio * (0.9 / max_final)
                print(f"音量調整: {max_final:.3f} → 0.9")
            
            # バックグラウンドで再生
            import sounddevice as sd
            sd.play(final_audio, sample_rate, blocking=False)
            
            print(f"連続再生完了: 総時間 {len(final_audio)/sample_rate:.1f}秒")
            
            # ボタンを元に戻す
            self.sequential_play_btn.setEnabled(True)
            self.sequential_play_btn.setText("連続して再生")
            
        except Exception as e:
            print(f"連続再生エラー: {str(e)}")
            self.sequential_play_btn.setEnabled(True)
            self.sequential_play_btn.setText("連続して再生")
    
    def save_individual(self):
        """個別保存（フォルダ内に個別ファイル）"""
        if not self.tts_engine.is_loaded:
            print("モデルが読み込まれていません")
            return
        
        texts_data = self.multi_text.get_all_texts_and_parameters()
        if not texts_data:
            print("テキストを入力してください")
            return
        
        try:
            import soundfile as sf
            
            # フォルダ選択
            folder_path = QFileDialog.getExistingDirectory(
                self,
                "個別保存フォルダを選択"
            )
            
            if folder_path:
                # 保存ボタンを一時無効化
                self.save_individual_btn.setEnabled(False)
                self.save_individual_btn.setText("保存中...")
                
                # 各行を個別に保存
                for i, data in enumerate(texts_data, 1):
                    text = data['text']
                    row_id = data['row_id']
                    
                    # 対応するタブのパラメータを取得
                    tab_parameters = self.tabbed_emotion_control.get_parameters(row_id)
                    if not tab_parameters:
                        tab_parameters = {
                            'style': 'Neutral', 'style_weight': 1.0,
                            'length_scale': 0.85, 'pitch_scale': 1.0,
                            'intonation_scale': 1.0, 'sdp_ratio': 0.25, 'noise': 0.35
                        }
                    
                    print(f"個別保存 {i}: {text}")
                    sr, audio = self.tts_engine.synthesize(text, **tab_parameters)
                    
                    # ファイル名生成
                    safe_text = "".join(c for c in text[:20] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    if not safe_text:
                        safe_text = f"text_{i}"
                    filename = f"{i:02d}_{safe_text}.wav"
                    file_path = os.path.join(folder_path, filename)
                    
                    sf.write(file_path, audio, sr)
                    print(f"保存完了: {filename}")
                
                print(f"個別保存完了: {len(texts_data)}ファイル → {folder_path}")
                
                # ボタンを元に戻す
                self.save_individual_btn.setEnabled(True)
                self.save_individual_btn.setText("個別保存")
                
        except Exception as e:
            print(f"個別保存エラー: {str(e)}")
            self.save_individual_btn.setEnabled(True)
            self.save_individual_btn.setText("個別保存")
    
    def save_continuous(self):
        """連続保存（1つのWAVファイルに統合）"""
        if not self.tts_engine.is_loaded:
            print("モデルが読み込まれていません")
            return
        
        texts_data = self.multi_text.get_all_texts_and_parameters()
        if not texts_data:
            print("テキストを入力してください")
            return
        
        try:
            import soundfile as sf
            import numpy as np
            
            # ファイル保存先選択
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "連続音声ファイルを保存",
                "continuous_output.wav",
                "WAV files (*.wav);;All files (*.*)"
            )
            
            if file_path:
                # 保存ボタンを一時無効化
                self.save_continuous_btn.setEnabled(False)
                self.save_continuous_btn.setText("保存中...")
                
                # 全ての音声を合成
                all_audio = []
                sample_rate = None
                
                for i, data in enumerate(texts_data, 1):
                    text = data['text']
                    row_id = data['row_id']
                    
                    # 対応するタブのパラメータを取得
                    tab_parameters = self.tabbed_emotion_control.get_parameters(row_id)
                    if not tab_parameters:
                        tab_parameters = {
                            'style': 'Neutral', 'style_weight': 1.0,
                            'length_scale': 0.85, 'pitch_scale': 1.0,
                            'intonation_scale': 1.0, 'sdp_ratio': 0.25, 'noise': 0.35
                        }
                    
                    print(f"連続保存合成 {i}/{len(texts_data)}: {text}")
                    sr, audio = self.tts_engine.synthesize(text, **tab_parameters)
                    
                    if sample_rate is None:
                        sample_rate = sr
                    
                    all_audio.append(audio)
                
                # 音声を結合（末尾無音削除）
                combined_audio = []
                for i, audio in enumerate(all_audio):
                    # 音声データをfloat32に正規化
                    if audio.dtype != np.float32:
                        audio = audio.astype(np.float32)
                    
                    # 音量を制限（クリッピング防止）
                    max_val = np.abs(audio).max()
                    if max_val > 0.8:
                        audio = audio * (0.8 / max_val)
                    
                    # 末尾無音を削除
                    audio = self.trim_silence(audio, sample_rate)
                    
                    combined_audio.append(audio)
                
                final_audio = np.concatenate(combined_audio).astype(np.float32)
                
                # 最終的なクリッピング防止
                max_final = np.abs(final_audio).max()
                if max_final > 0.9:
                    final_audio = final_audio * (0.9 / max_final)
                    print(f"保存時音量調整: {max_final:.3f} → 0.9")
                
                # ファイル保存
                sf.write(file_path, final_audio, sample_rate)
                print(f"連続保存完了: {file_path} ({len(final_audio)/sample_rate:.1f}秒)")
                
                # ボタンを元に戻す
                self.save_continuous_btn.setEnabled(True)
                self.save_continuous_btn.setText("連続保存")
                
        except Exception as e:
            print(f"連続保存エラー: {str(e)}")
            self.save_continuous_btn.setEnabled(True)
            self.save_continuous_btn.setText("連続保存")