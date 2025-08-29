from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                            QComboBox, QDoubleSpinBox, QGroupBox, QGridLayout, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class EmotionControlWidget(QWidget):
    """感情・パラメータ制御ウィジェット"""
    
    # パラメータ変更シグナル
    parameters_changed = pyqtSignal(dict)
    
    def __init__(self, tts_engine=None, parent=None):
        super().__init__(parent)
        
        self.tts_engine = tts_engine
        
        # 現在のパラメータ
        self.current_params = {
            'style': 'Neutral',
            'style_weight': 1.0,
            'sdp_ratio': 0.25,
            'noise': 0.35,
            'length_scale': 0.85
        }
        
        self.init_ui()
        
    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 感情制御グループ
        emotion_group = self.create_emotion_group()
        layout.addWidget(emotion_group)
        
        # 音声パラメータグループ
        params_group = self.create_params_group()
        layout.addWidget(params_group)
        
        # プリセットボタン
        preset_group = self.create_preset_group()
        layout.addWidget(preset_group)
        
        layout.addStretch()  # 下部の余白
        
    def create_emotion_group(self):
        """感情制御グループを作成"""
        group = QGroupBox("感情制御")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # 感情選択
        emotion_layout = QHBoxLayout()
        emotion_label = QLabel("感情:")
        emotion_label.setMinimumWidth(80)
        
        self.emotion_combo = QComboBox()
        
        # TTSエンジンから感情リストを取得
        if self.tts_engine and self.tts_engine.is_loaded:
            available_emotions = self.tts_engine.get_available_styles()
        else:
            available_emotions = ["Neutral"]
        
        # 感情マッピング（表示用）
        emotion_display = {
            "Neutral": "😐 ニュートラル",
            "Happy": "😊 喜び",
            "Sad": "😢 悲しみ", 
            "Angry": "😠 怒り",
            "Fear": "😰 恐怖",
            "Disgust": "😖 嫌悪",
            "Surprise": "😲 驚き"
        }
        
        for emotion in available_emotions:
            display_name = emotion_display.get(emotion, f"📢 {emotion}")
            self.emotion_combo.addItem(display_name, emotion)
        
        self.emotion_combo.currentTextChanged.connect(self.on_emotion_changed)
        
        emotion_layout.addWidget(emotion_label)
        emotion_layout.addWidget(self.emotion_combo, 1)
        
        # 感情強度
        intensity_layout = QHBoxLayout()
        intensity_label = QLabel("感情強度:")
        intensity_label.setMinimumWidth(80)
        
        # スライダー
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 200)  # 0.0 ~ 2.0
        self.intensity_slider.setValue(100)  # 1.0
        self.intensity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #66e, stop: 1 #bbf);
                border: 1px solid #777;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #eee, stop: 1 #ccc);
                border: 1px solid #777;
                width: 18px;
                margin-top: -6px;
                margin-bottom: -6px;
                border-radius: 9px;
            }
        """)
        self.intensity_slider.valueChanged.connect(self.on_intensity_slider_changed)
        
        # 数値入力
        self.intensity_spinbox = QDoubleSpinBox()
        self.intensity_spinbox.setRange(0.0, 2.0)
        self.intensity_spinbox.setSingleStep(0.1)
        self.intensity_spinbox.setValue(1.0)
        self.intensity_spinbox.setDecimals(2)
        self.intensity_spinbox.setFixedWidth(70)
        self.intensity_spinbox.valueChanged.connect(self.on_intensity_spinbox_changed)
        
        intensity_layout.addWidget(intensity_label)
        intensity_layout.addWidget(self.intensity_slider, 1)
        intensity_layout.addWidget(self.intensity_spinbox)
        
        layout.addLayout(emotion_layout)
        layout.addLayout(intensity_layout)
        
        return group
    
    def create_params_group(self):
        """音声パラメータグループを作成"""
        group = QGroupBox("音声パラメータ")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(8)
        
        # パラメータ定義
        params = [
            ("話速", "length_scale", 0.3, 1.8, 0.85, "超速い ← → 超遅い"),
            ("ピッチ変動", "sdp_ratio", 0.0, 0.5, 0.25, "単調 ← → 抑揚"),
            ("ノイズ", "noise", 0.1, 0.7, 0.35, "クリア ← → 自然")
        ]
        
        self.param_sliders = {}
        self.param_spinboxes = {}
        
        for i, (name, key, min_val, max_val, default, desc) in enumerate(params):
            # ラベル
            label = QLabel(name + ":")
            label.setMinimumWidth(80)
            
            # スライダー
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(int(min_val * 100), int(max_val * 100))
            slider.setValue(int(default * 100))
            slider.setStyleSheet(self.intensity_slider.styleSheet())
            
            # 数値入力
            spinbox = QDoubleSpinBox()
            spinbox.setRange(min_val, max_val)
            spinbox.setSingleStep(0.01)
            spinbox.setValue(default)
            spinbox.setDecimals(2)
            spinbox.setFixedWidth(70)
            
            # 説明
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #666; font-size: 9pt;")
            
            # イベント接続
            slider.valueChanged.connect(lambda v, k=key: self.on_param_slider_changed(k, v))
            spinbox.valueChanged.connect(lambda v, k=key: self.on_param_spinbox_changed(k, v))
            
            # 保存
            self.param_sliders[key] = slider
            self.param_spinboxes[key] = spinbox
            
            # レイアウトに追加
            layout.addWidget(label, i, 0)
            layout.addWidget(slider, i, 1)
            layout.addWidget(spinbox, i, 2)
            layout.addWidget(desc_label, i, 3)
        
        return group
    
    def create_preset_group(self):
        """プリセットボタングループを作成"""
        group = QGroupBox("プリセット")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(5)
        
        # プリセット定義
        presets = [
            ("標準", {'style': 'Neutral', 'style_weight': 1.0, 'sdp_ratio': 0.25, 'noise': 0.35, 'length_scale': 0.85}),
            ("元気", {'style': 'Happy', 'style_weight': 1.2, 'sdp_ratio': 0.3, 'noise': 0.4, 'length_scale': 0.6}),  # 速く
            ("落ち着き", {'style': 'Neutral', 'style_weight': 0.8, 'sdp_ratio': 0.2, 'noise': 0.3, 'length_scale': 1.2}),  # 遅く
            ("感情豊か", {'style': 'Happy', 'style_weight': 1.5, 'sdp_ratio': 0.35, 'noise': 0.45, 'length_scale': 0.75}),
        ]
        
        for i, (name, params) in enumerate(presets):
            btn = QPushButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #e3f2fd;
                    border-color: #2196f3;
                }
                QPushButton:pressed {
                    background-color: #bbdefb;
                }
            """)
            btn.clicked.connect(lambda checked, p=params: self.apply_preset(p))
            
            row = i // 2
            col = i % 2
            layout.addWidget(btn, row, col)
        
        return group
    
    def on_emotion_changed(self, text):
        """感情変更時の処理"""
        # コンボボックスのデータから実際の値を取得
        current_data = self.emotion_combo.currentData()
        if current_data:
            self.current_params['style'] = current_data
            self.emit_parameters_changed()
    
    def on_intensity_slider_changed(self, value):
        """感情強度スライダー変更時"""
        float_value = value / 100.0
        self.intensity_spinbox.blockSignals(True)
        self.intensity_spinbox.setValue(float_value)
        self.intensity_spinbox.blockSignals(False)
        
        self.current_params['style_weight'] = float_value
        self.emit_parameters_changed()
    
    def on_intensity_spinbox_changed(self, value):
        """感情強度数値入力変更時"""
        int_value = int(value * 100)
        self.intensity_slider.blockSignals(True)
        self.intensity_slider.setValue(int_value)
        self.intensity_slider.blockSignals(False)
        
        self.current_params['style_weight'] = value
        self.emit_parameters_changed()
    
    def on_param_slider_changed(self, param_key, value):
        """パラメータスライダー変更時"""
        float_value = value / 100.0
        
        # 対応するスピンボックスを更新
        spinbox = self.param_spinboxes[param_key]
        spinbox.blockSignals(True)
        spinbox.setValue(float_value)
        spinbox.blockSignals(False)
        
        self.current_params[param_key] = float_value
        self.emit_parameters_changed()
    
    def on_param_spinbox_changed(self, param_key, value):
        """パラメータ数値入力変更時"""
        int_value = int(value * 100)
        
        # 対応するスライダーを更新
        slider = self.param_sliders[param_key]
        slider.blockSignals(True)
        slider.setValue(int_value)
        slider.blockSignals(False)
        
        self.current_params[param_key] = value
        self.emit_parameters_changed()
    
    def apply_preset(self, preset_params):
        """プリセットを適用"""
        self.current_params.update(preset_params)
        
        # UI要素を更新（シグナルをブロックして無限ループ防止）
        self.blockSignals(True)
        
        # 感情
        for i in range(self.emotion_combo.count()):
            if self.emotion_combo.itemData(i) == preset_params['style']:
                self.emotion_combo.setCurrentIndex(i)
                break
        
        # 感情強度
        style_weight = preset_params['style_weight']
        self.intensity_slider.setValue(int(style_weight * 100))
        self.intensity_spinbox.setValue(style_weight)
        
        # その他のパラメータ
        for key, value in preset_params.items():
            if key in self.param_sliders:
                self.param_sliders[key].setValue(int(value * 100))
                self.param_spinboxes[key].setValue(value)
        
        self.blockSignals(False)
        
        # パラメータ変更を通知
        self.emit_parameters_changed()
    
    def emit_parameters_changed(self):
        """パラメータ変更シグナルを送信"""
        self.parameters_changed.emit(self.current_params.copy())
    
    def get_current_parameters(self):
        """現在のパラメータを取得"""
        return self.current_params.copy()
    
    def set_parameters(self, params):
        """パラメータを設定"""
        self.apply_preset(params)
    
    def set_tts_engine(self, tts_engine):
        """TTSエンジンを設定し、感情リストを更新"""
        self.tts_engine = tts_engine
        self.refresh_emotions()
    
    def refresh_emotions(self):
        """感情リストを更新"""
        if not self.tts_engine or not self.tts_engine.is_loaded:
            return
        
        current_emotion = self.emotion_combo.currentData()
        self.emotion_combo.clear()
        
        available_emotions = self.tts_engine.get_available_styles()
        
        emotion_display = {
            "Neutral": "😐 ニュートラル",
            "Happy": "😊 喜び",
            "Sad": "😢 悲しみ", 
            "Angry": "😠 怒り",
            "Fear": "😰 恐怖",
            "Disgust": "😖 嫌悪",
            "Surprise": "😲 驚き"
        }
        
        for emotion in available_emotions:
            display_name = emotion_display.get(emotion, f"📢 {emotion}")
            self.emotion_combo.addItem(display_name, emotion)
        
        # 前の選択を復元
        if current_emotion:
            for i in range(self.emotion_combo.count()):
                if self.emotion_combo.itemData(i) == current_emotion:
                    self.emotion_combo.setCurrentIndex(i)
                    break