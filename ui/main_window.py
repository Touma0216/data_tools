import os
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QFileDialog, QStyle, QFrame, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction

# 自作モジュール
from .model_history import ModelHistoryWidget
from .model_loader import ModelLoaderDialog
from .tabbed_emotion_control import TabbedEmotionControl
from .multi_text import MultiTextWidget
from core.tts_engine import TTSEngine
from core.model_manager import ModelManager

class TTSStudioMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tts_engine = TTSEngine()
        self.model_manager = ModelManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("TTSスタジオ - ほのかちゃん")
        self.setGeometry(100, 100, 1200, 800)
        self.create_menu_bar()

        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setSpacing(10)
        main.setContentsMargins(15, 15, 15, 15)

        content = QHBoxLayout()

        # 左ペイン
        left = QVBoxLayout()
        self.multi_text = MultiTextWidget()
        self.multi_text.play_single_requested.connect(self.play_single_text)
        self.multi_text.row_added.connect(self.on_text_row_added)
        self.multi_text.row_removed.connect(self.on_text_row_removed)
        self.multi_text.row_numbers_updated.connect(self.on_row_numbers_updated)

        params_label = QLabel("音声パラメータ:")
        params_label.setFont(QFont("", 10, QFont.Weight.Bold))

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("color: #dee2e6;")

        self.tabbed_emotion_control = TabbedEmotionControl()
        self.tabbed_emotion_control.parameters_changed.connect(self.on_parameters_changed)
        self.tabbed_emotion_control.add_text_row("initial", 1)

        controls = QHBoxLayout()
        controls.addStretch()

        self.sequential_play_btn = QPushButton("連続して再生")
        self.sequential_play_btn.setMinimumHeight(35)
        self.sequential_play_btn.setEnabled(False)
        self.sequential_play_btn.setStyleSheet(self._gray_btn_css())
        self.sequential_play_btn.clicked.connect(self.play_sequential)

        self.save_individual_btn = QPushButton("個別保存")
        self.save_individual_btn.setMinimumHeight(35)
        self.save_individual_btn.setEnabled(False)
        self.save_individual_btn.setStyleSheet(self._gray_btn_css())
        self.save_individual_btn.clicked.connect(self.save_individual)

        self.save_continuous_btn = QPushButton("連続保存")
        self.save_continuous_btn.setMinimumHeight(35)
        self.save_continuous_btn.setEnabled(False)
        self.save_continuous_btn.setStyleSheet(self._gray_btn_css())
        self.save_continuous_btn.clicked.connect(self.save_continuous)

        controls.addWidget(self.sequential_play_btn)
        controls.addWidget(self.save_individual_btn)
        controls.addWidget(self.save_continuous_btn)

        left.addWidget(self.multi_text, 1)
        left.addWidget(params_label)
        left.addWidget(divider)
        left.addWidget(self.tabbed_emotion_control, 1)
        left.addLayout(controls)

        # 右ペイン（ダミー）
        self.live2d_widget = QWidget()
        self.live2d_widget.setMaximumWidth(300)
        self.live2d_widget.setMinimumWidth(250)
        self.live2d_widget.setStyleSheet("""
            QWidget { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 4px; }
        """)
        live2d_layout = QVBoxLayout(self.live2d_widget)
        live2d_label = QLabel("Live2D\nリップシンクエリア")
        live2d_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        live2d_label.setStyleSheet("color: #666; font-size: 14px; border: none;")
        live2d_layout.addWidget(live2d_label)

        content.addLayout(left, 1)
        content.addWidget(self.live2d_widget, 0)
        main.addLayout(content)

    def _gray_btn_css(self) -> str:
        return """
            QPushButton {
                background-color: #f0f0f0; color: #333333;
                border: 1px solid #cccccc; border-radius: 4px;
                font-size: 13px; font-weight: bold; padding: 0 16px;
            }
            QPushButton:hover:enabled { background-color: #e0e0e0; }
            QPushButton:pressed:enabled { background-color: #d0d0d0; }
            QPushButton:disabled {
                background-color: #f8f8f8; color: #aaaaaa; border: 1px solid #e5e5e5;
            }
        """

    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar { background-color: #f8f9fa; color: #333; border-bottom: 1px solid #dee2e6; padding: 4px; }
            QMenuBar::item { background-color: transparent; padding: 6px 12px; margin: 0px 2px; border-radius: 4px; }
            QMenuBar::item:selected { background-color: #e9ecef; }
            QMenuBar::item:pressed { background-color: #dee2e6; }
            QMenu { background-color: white; border: 1px solid #dee2e6; border-radius: 6px; padding: 4px 0px; }
            QMenu::item { padding: 8px 20px; margin: 2px 4px; border-radius: 4px; }
            QMenu::item:selected { background-color: #e3f2fd; color: #1976d2; }
            QMenu::separator { height: 1px; background-color: #dee2e6; margin: 4px 8px; }
        """)

        file_menu = menubar.addMenu("ファイル")

        load_model_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon), "モデルを読み込み", self)
        load_model_action.setStatusTip("Style-Bert-VITS2モデルを読み込む")
        load_model_action.triggered.connect(self.open_model_loader)
        file_menu.addAction(load_model_action)

        file_menu.addSeparator()

        load_from_history_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DriveFDIcon), "モデル履歴から読み込み", self)
        load_from_history_action.setStatusTip("過去に読み込んだモデルから選択")
        load_from_history_action.triggered.connect(self.show_model_history_dialog)
        file_menu.addAction(load_from_history_action)

    # ---------- 履歴ダイアログ ----------
    def open_model_loader(self):
        dialog = ModelLoaderDialog(self)
        dialog.model_loaded.connect(self.load_model)
        dialog.exec()

    def show_model_history_dialog(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QMessageBox

        if not self.model_manager.get_all_models():
            QMessageBox.information(self, "履歴なし", "モデル履歴がありません。")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("モデル履歴から選択")
        dlg.setModal(True)
        dlg.resize(560, 420)
        dlg.setStyleSheet("QDialog { background:#f8f9fa; }")

        lay = QVBoxLayout(dlg)
        widget = ModelHistoryWidget(self.model_manager, dlg)

        def _on_selected(model_data):
            if not self.model_manager.validate_model_files(model_data):
                QMessageBox.warning(dlg, "エラー", "モデルファイルが見つかりません。")
                return
            paths = {
                'model_path': model_data['model_path'],
                'config_path': model_data['config_path'],
                'style_path': model_data['style_path'],
            }
            dlg.accept()
            self.load_model(paths)
            self.model_manager.update_last_used(model_data['id'])

        widget.model_selected.connect(_on_selected)
        lay.addWidget(widget)
        dlg.exec()

    # ---------- TTS / そのほか（既存） ----------
    def on_text_row_added(self, row_id, row_number):
        self.tabbed_emotion_control.add_text_row(row_id, row_number)

    def on_text_row_removed(self, row_id):
        self.tabbed_emotion_control.remove_text_row(row_id)

    def on_row_numbers_updated(self, row_mapping):
        self.tabbed_emotion_control.update_tab_numbers(row_mapping)

    def load_model(self, paths):
        success = self.tts_engine.load_model(paths['model_path'], paths['config_path'], paths['style_path'])
        if success:
            # 履歴に追加（名前は ModelManager 側で親フォルダ名へ整形）
            self.model_manager.add_model(paths['model_path'], paths['config_path'], paths['style_path'])
            self.sequential_play_btn.setEnabled(True)
            self.save_individual_btn.setEnabled(True)
            self.save_continuous_btn.setEnabled(True)
        else:
            self.sequential_play_btn.setEnabled(False)
            self.save_individual_btn.setEnabled(False)
            self.save_continuous_btn.setEnabled(False)

    # 以下、既存の synth / save 系はそのまま（省略なしで使ってOK）
    def on_parameters_changed(self, row_id, params):
        print(f"行 {row_id} のパラメータ更新: {params}")

    def play_single_text(self, row_id, text, parameters):
        if not self.tts_engine.is_loaded:
            print("モデルが読み込まれていません")
            return
        tab_parameters = self.tabbed_emotion_control.get_parameters(row_id) or parameters
        try:
            print(f"行 {row_id} を再生: {text}")
            sr, audio = self.tts_engine.synthesize(text, **tab_parameters)
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