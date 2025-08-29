from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QListWidgetItem, QPushButton, QLabel, QLineEdit, 
                            QDialog, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
import os

class ModelHistoryItem(QWidget):
    """履歴アイテムのカスタムウィジェット"""
    load_requested = pyqtSignal(str)  # model_id
    edit_requested = pyqtSignal(str)  # model_id
    delete_requested = pyqtSignal(str)  # model_id
    
    def __init__(self, model_data, parent=None):
        super().__init__(parent)
        self.model_data = model_data
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(8)
        
        # モデル情報部分
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # モデル名
        name_label = QLabel(self.model_data['name'])
        name_label.setFont(QFont("", 10, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #333;")
        
        # 詳細情報
        details = []
        if 'last_used' in self.model_data:
            from core.model_manager import ModelManager
            manager = ModelManager()
            last_used = manager.get_formatted_datetime(self.model_data['last_used'])
            details.append(f"最終使用: {last_used}")
        
        if 'use_count' in self.model_data:
            details.append(f"使用回数: {self.model_data['use_count']}回")
        
        detail_text = " | ".join(details)
        detail_label = QLabel(detail_text)
        detail_label.setStyleSheet("color: #666; font-size: 9pt;")
        
        # パス表示（短縮版）
        model_path = self.model_data['model_path']
        short_path = "..." + model_path[-40:] if len(model_path) > 40 else model_path
        path_label = QLabel(short_path)
        path_label.setStyleSheet("color: #888; font-size: 8pt;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(detail_label)
        info_layout.addWidget(path_label)
        
        # ボタン部分
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        
        # 編集ボタン
        edit_btn = QPushButton("✏")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffb300;
            }
        """)
        edit_btn.setToolTip("名前を編集")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.model_data['id']))
        
        # 削除ボタン
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.setToolTip("履歴から削除")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.model_data['id']))
        
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        
        # 読み込みボタン（メイン）
        load_btn = QPushButton("読み込み")
        load_btn.setFixedSize(70, 32)
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        load_btn.clicked.connect(lambda: self.load_requested.emit(self.model_data['id']))
        
        # レイアウト組み立て
        layout.addLayout(info_layout, 1)  # 伸縮
        layout.addLayout(button_layout, 0)
        layout.addWidget(load_btn, 0)
        
        # ファイル存在チェック
        if not self._check_files_exist():
            self.setStyleSheet("background-color: #ffebee; border-left: 3px solid #f44336;")
            load_btn.setEnabled(False)
            load_btn.setText("削除済み")
            load_btn.setStyleSheet("""
                QPushButton {
                    background-color: #cccccc;
                    color: #666666;
                    border: none;
                    border-radius: 4px;
                    font-size: 9px;
                }
            """)
        else:
            self.setStyleSheet("background-color: white; border: 1px solid #eee; border-radius: 4px;")
    
    def _check_files_exist(self):
        """ファイルの存在確認"""
        paths = [
            self.model_data['model_path'],
            self.model_data['config_path'],
            self.model_data['style_path']
        ]
        return all(os.path.exists(path) for path in paths)

class ModelHistoryWidget(QWidget):
    """モデル履歴表示ウィジェット"""
    model_selected = pyqtSignal(dict)  # 選択されたモデルデータ
    
    def __init__(self, model_manager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.init_ui()
        self.refresh_list()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # ヘッダー
        header = QLabel("モデル履歴")
        header.setFont(QFont("", 10, QFont.Weight.Bold))
        header.setStyleSheet("color: #333; padding: 5px 0;")
        
        # 履歴リスト
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fafafa;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
                padding: 0;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
        """)
        
        # フッター（クリアボタンなど）
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        clear_btn = QPushButton("履歴をクリア")
        clear_btn.setStyleSheet("""
            QPushButton {
                color: #666;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        clear_btn.clicked.connect(self.clear_history)
        footer_layout.addWidget(clear_btn)
        
        layout.addWidget(header)
        layout.addWidget(self.history_list, 1)
        layout.addLayout(footer_layout)
    
    def refresh_list(self):
        """履歴リストを更新"""
        self.history_list.clear()
        
        models = self.model_manager.get_all_models()
        if not models:
            # 空の場合
            empty_item = QListWidgetItem()
            empty_widget = QLabel("履歴がありません")
            empty_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_widget.setStyleSheet("color: #999; padding: 20px;")
            
            self.history_list.addItem(empty_item)
            self.history_list.setItemWidget(empty_item, empty_widget)
            return
        
        # 履歴アイテムを追加
        for model_data in models:
            list_item = QListWidgetItem()
            history_item = ModelHistoryItem(model_data)
            
            # シグナル接続
            history_item.load_requested.connect(self.load_model)
            history_item.edit_requested.connect(self.edit_model_name)
            history_item.delete_requested.connect(self.delete_model)
            
            list_item.setSizeHint(history_item.sizeHint())
            self.history_list.addItem(list_item)
            self.history_list.setItemWidget(list_item, history_item)
    
    def load_model(self, model_id):
        """モデルを読み込み"""
        model_data = self.model_manager.get_model_by_id(model_id)
        if model_data:
            # 最終使用日時を更新
            self.model_manager.update_last_used(model_id)
            # シグナル送信
            self.model_selected.emit(model_data)
            self.refresh_list()  # リスト更新
    
    def edit_model_name(self, model_id):
        """モデル名を編集"""
        model_data = self.model_manager.get_model_by_id(model_id)
        if not model_data:
            return
        
        current_name = model_data['name']
        
        # 簡易入力ダイアログ
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, 
            "モデル名を編集", 
            "新しいモデル名:", 
            text=current_name
        )
        
        if ok and new_name.strip():
            self.model_manager.update_model_name(model_id, new_name.strip())
            self.refresh_list()
    
    def delete_model(self, model_id):
        """モデルを削除"""
        model_data = self.model_manager.get_model_by_id(model_id)
        if not model_data:
            return
        
        # 確認なし（UXのため）
        self.model_manager.remove_model(model_id)
        self.refresh_list()
    
    def clear_history(self):
        """履歴をクリア"""
        reply = QMessageBox.question(
            self, 
            "確認", 
            "すべての履歴を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.model_manager.models = []
            self.model_manager.save_history()
            self.refresh_list()