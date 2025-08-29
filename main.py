import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# 自作モジュール
from ui.model_loader import ModelLoaderDialog
from ui.model_history import ModelHistoryWidget
from ui.emotion_control import EmotionControlWidget
from core.tts_engine import TTSEngine
from core.model_manager import ModelManager

class TTSStudioMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # TTSエンジン初期化
        self.tts_engine = TTSEngine()
        
        # モデル管理初期化
        self.model_manager = ModelManager()
        
        # 現在の音声パラメータ
        self.current_audio_params = {}
        
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウ設定
        self.setWindowTitle("TTSスタジオ - ほのかちゃん")
        self.setGeometry(100, 100, 1000, 700)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ヘッダー部分（モデル読み込み関連）
        header_layout = QHBoxLayout()
        
        # モデル状態表示
        self.model_status_label = QLabel("モデル: 未読み込み")
        self.model_status_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #ffebee;
                border: 1px solid #e57373;
                border-radius: 4px;
                color: #d32f2f;
                font-weight: bold;
            }
        """)
        
        # モデル読み込みボタン
        self.load_model_btn = QPushButton("モデルを読み込み")
        self.load_model_btn.setMinimumHeight(40)
        self.load_model_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.load_model_btn.clicked.connect(self.open_model_loader)
        
        header_layout.addWidget(self.model_status_label, 1)
        header_layout.addWidget(self.load_model_btn, 0)
        
        # メインコンテンツエリア
        content_layout = QHBoxLayout()
        
        # 左側: テキスト入力とコントロール
        left_layout = QVBoxLayout()
        
        # テキスト入力エリア
        text_label = QLabel("テキスト入力:")
        text_label.setFont(QFont("", 10, QFont.Weight.Bold))
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("ここに読み上げたいテキストを入力してください...")
        self.text_input.setMinimumHeight(150)
        self.text_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        
        # パラメータエリア
        params_label = QLabel("音声パラメータ:")
        params_label.setFont(QFont("", 10, QFont.Weight.Bold))
        
        # 感情制御ウィジェット
        self.emotion_control = EmotionControlWidget(self.tts_engine)
        self.emotion_control.parameters_changed.connect(self.on_parameters_changed)
        
        # 制御ボタン
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ 再生")
        self.save_btn = QPushButton("💾 保存")
        
        for btn in [self.play_btn, self.save_btn]:
            btn.setMinimumHeight(40)
            btn.setEnabled(False)  # 最初は無効
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover:enabled {
                    background-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """)
        
        self.play_btn.clicked.connect(self.play_audio)
        self.save_btn.clicked.connect(self.save_audio)
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.save_btn)
        
        # 左側レイアウト組み立て
        left_layout.addWidget(text_label)
        left_layout.addWidget(self.text_input)
        left_layout.addWidget(params_label)
        left_layout.addWidget(self.emotion_control, 1)  # 伸縮可能
        left_layout.addLayout(controls_layout)
        
        # 右側: モデル履歴
        self.model_history = ModelHistoryWidget(self.model_manager)
        self.model_history.model_selected.connect(self.load_model_from_history)
        self.model_history.setMaximumWidth(300)
        self.model_history.setMinimumWidth(250)
        
        # メインコンテンツレイアウト
        content_layout.addLayout(left_layout, 1)  # 左側が伸縮
        content_layout.addWidget(self.model_history, 0)  # 右側は固定幅
        
        # レイアウトに追加
        main_layout.addLayout(header_layout)
        main_layout.addLayout(content_layout)
        
    def open_model_loader(self):
        """モデル読み込みダイアログを開く"""
        dialog = ModelLoaderDialog(self)
        dialog.model_loaded.connect(self.load_model)
        dialog.exec()
        
    def load_model(self, paths):
        """モデルを読み込む"""
        self.update_model_status("読み込み中...", False)
        
        # 別スレッドでモデル読み込み（UIフリーズ防止）
        success = self.tts_engine.load_model(
            paths['model_path'],
            paths['config_path'], 
            paths['style_path']
        )
        
        if success:
            model_name = Path(paths['model_path']).stem
            self.update_model_status(f"読み込み完了 ({model_name})", True)
            
            # モデルを履歴に追加
            self.model_manager.add_model(
                paths['model_path'],
                paths['config_path'],
                paths['style_path']
            )
            
            # 履歴リストを更新
            self.model_history.refresh_list()
            
            # 感情リストを更新
            self.emotion_control.set_tts_engine(self.tts_engine)
        else:
            self.update_model_status("読み込み失敗", False)
    
    def load_model_from_history(self, model_data):
        """履歴からモデルを読み込む"""
        paths = {
            'model_path': model_data['model_path'],
            'config_path': model_data['config_path'],
            'style_path': model_data['style_path']
        }
        self.load_model(paths)
    
    def on_parameters_changed(self, params):
        """感情制御パラメータが変更された時の処理"""
        self.current_audio_params = params
        print(f"パラメータ更新: {params}")
    
    def play_audio(self):
        """音声を再生"""
        if not self.tts_engine.is_loaded:
            print("モデルが読み込まれていません")
            return
            
        text = self.text_input.toPlainText().strip()
        if not text:
            print("テキストを入力してください")
            return
        
        try:
            # 再生ボタンを一時無効化
            self.play_btn.setEnabled(False)
            self.play_btn.setText("再生中...")
            
            # 音声合成
            sr, audio = self.tts_engine.synthesize(text, **self.current_audio_params)
            
            # バックグラウンドで再生
            import sounddevice as sd
            sd.play(audio, sr, blocking=False)  # non-blocking再生
            
            # ボタンを元に戻す
            self.play_btn.setEnabled(True)
            self.play_btn.setText("▶ 再生")
            
        except Exception as e:
            print(f"音声合成エラー: {str(e)}")
            self.play_btn.setEnabled(True)
            self.play_btn.setText("▶ 再生")
    
    def save_audio(self):
        """音声をファイルに保存"""
        if not self.tts_engine.is_loaded:
            print("モデルが読み込まれていません")
            return
            
        text = self.text_input.toPlainText().strip()
        if not text:
            print("テキストを入力してください")
            return
        
        try:
            from PyQt6.QtWidgets import QFileDialog
            import soundfile as sf
            
            # 保存先選択
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "音声ファイルを保存",
                "output.wav",
                "WAV files (*.wav);;All files (*.*)"
            )
            
            if file_path:
                # 保存ボタンを一時無効化
                self.save_btn.setEnabled(False)
                self.save_btn.setText("保存中...")
                
                # 音声合成
                sr, audio = self.tts_engine.synthesize(text, **self.current_audio_params)
                
                # ファイル保存
                sf.write(file_path, audio, sr)
                print(f"音声ファイルを保存: {file_path}")
                
                # ボタンを元に戻す
                self.save_btn.setEnabled(True)
                self.save_btn.setText("💾 保存")
                
        except Exception as e:
            print(f"保存エラー: {str(e)}")
            self.save_btn.setEnabled(True)
            self.save_btn.setText("💾 保存")
        
    def update_model_status(self, status_text, is_loaded=False):
        """モデル読み込み状態を更新"""
        self.model_status_label.setText(f"モデル: {status_text}")
        
        if is_loaded:
            # 読み込み成功
            self.model_status_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 4px;
                    color: #2e7d32;
                    font-weight: bold;
                }
            """)
            # ボタンを有効化
            self.play_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
        else:
            # 読み込み失敗または未読み込み
            self.model_status_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    background-color: #ffebee;
                    border: 1px solid #e57373;
                    border-radius: 4px;
                    color: #d32f2f;
                    font-weight: bold;
                }
            """)
            # ボタンを無効化
            self.play_btn.setEnabled(False)
            self.save_btn.setEnabled(False)

def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # アプリケーション情報
    app.setApplicationName("TTSスタジオ")
    app.setApplicationVersion("1.0.0")
    
    # メインウィンドウ作成・表示
    window = TTSStudioMainWindow()
    window.show()
    
    # イベントループ開始
    sys.exit(app.exec())

if __name__ == "__main__":
    main()