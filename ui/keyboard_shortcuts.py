from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QObject

class KeyboardShortcutManager(QObject):
    """キーボードショートカット管理クラス"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.shortcuts = {}
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        """全ショートカットを設定"""
        
        # ファイルメニュー
        self.add_shortcut("F", self.open_file_menu)
        
        # 再生系
        self.add_shortcut("R", self.play_current_row)
        self.add_shortcut("Ctrl+R", self.play_sequential)
        
        # テキスト操作
        self.add_shortcut("N", self.add_text_row)
        
        # テキスト行選択（1-9）
        for i in range(1, 10):
            self.add_shortcut(str(i), lambda row_num=i: self.focus_text_row(row_num))
        
        # 感情選択
        self.add_shortcut("E", self.open_emotion_combo)
        
        # 保存系
        self.add_shortcut("Ctrl+S", self.save_individual)
        self.add_shortcut("Ctrl+Shift+S", self.save_continuous)
    
    def add_shortcut(self, key_sequence, callback):
        """ショートカットを追加"""
        shortcut = QShortcut(QKeySequence(key_sequence), self.main_window)
        shortcut.activated.connect(callback)
        self.shortcuts[key_sequence] = shortcut
    
    # ========================
    # ショートカット実行関数
    # ========================
    
    def open_file_menu(self):
        """ファイルメニューを開く"""
        self.main_window.toggle_file_menu()
    
    def play_current_row(self):
        """現在フォーカス中の行を再生"""
        # アクティブなタブのIDを取得
        current_tab_index = self.main_window.tabbed_emotion_control.tab_widget.currentIndex()
        if current_tab_index >= 0:
            # タブのrow_idを取得（タブウィジェットから逆引き）
            current_control = self.main_window.tabbed_emotion_control.tab_widget.currentWidget()
            if current_control and hasattr(current_control, 'row_id'):
                row_id = current_control.row_id
                # 対応するテキスト行を再生
                if row_id in self.main_window.multi_text.text_rows:
                    text_widget = self.main_window.multi_text.text_rows[row_id]
                    text_widget.play_btn.click()
    
    def play_sequential(self):
        """連続再生"""
        self.main_window.sequential_play_btn.click()
    
    def add_text_row(self):
        """テキスト行を追加"""
        # 9行制限チェック
        if len(self.main_window.multi_text.text_rows) >= 9:
            return
        self.main_window.multi_text.add_text_row()
    
    def focus_text_row(self, row_number):
        """指定番号のテキスト行にフォーカス"""
        text_rows = list(self.main_window.multi_text.text_rows.values())
        if 0 < row_number <= len(text_rows):
            target_row = text_rows[row_number - 1]
            target_row.text_input.setFocus()
            
            # 対応するパラメータタブもアクティブに
            row_id = target_row.row_id
            self.main_window.tabbed_emotion_control.set_current_row(row_id)
    
    def open_emotion_combo(self):
        """感情コンボボックスを開く"""
        current_control = self.main_window.tabbed_emotion_control.tab_widget.currentWidget()
        if current_control and hasattr(current_control, 'emotion_combo'):
            current_control.emotion_combo.setFocus()
            current_control.emotion_combo.showPopup()
    
    def save_individual(self):
        """個別保存"""
        self.main_window.save_individual_btn.click()
    
    def save_continuous(self):
        """連続保存"""
        self.main_window.save_continuous_btn.click()