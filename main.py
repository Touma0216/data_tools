import sys
import logging
import warnings
from PyQt6.QtWidgets import QApplication

# 全てのログを無効化（最強設定）
logging.disable(logging.CRITICAL)

# 警告も無効化
warnings.filterwarnings("ignore")

# 新しいモジュールのインポート
from ui.main_window import TTSStudioMainWindow

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