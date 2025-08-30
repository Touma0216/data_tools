from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                            QComboBox, QDoubleSpinBox, QGroupBox, QGridLayout, QPushButton, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class SingleEmotionControl(QWidget):
    """単一行の感情制御ウィジェット"""
    
    parameters_changed = pyqtSignal(str, dict)  # row_id, parameters
    
    def __init__(self, row_id, parameters=None, parent=None):
        super().__init__(parent)
        
        self.row_id = row_id
        self.current_params = parameters or {
            'style': 'Neutral',
            'style_weight': 1.0,
            'length_scale': 0.85,
            'pitch_scale': 1.0,
            'intonation_scale': 1.0,
            'sdp_ratio': 0.25,
            'noise': 0.35
        }
        
        self.init_ui()
        self.load_parameters()
        
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
        
        layout.addStretch()
        
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
        self.emotion_combo.setToolTip("感情選択(E)")
        emotions = [
            ("Neutral", "😐 ニュートラル"),
            ("Happy", "😊 喜び"),
            ("Sad", "😢 悲しみ"), 
            ("Angry", "😠 怒り"),
            ("Fear", "😰 恐怖"),
            ("Disgust", "😖 嫌悪"),
            ("Surprise", "😲 驚き")
        ]
        
        for value, display in emotions:
            self.emotion_combo.addItem(display, value)
        
        self.emotion_combo.currentTextChanged.connect(self.on_emotion_changed)
        
        emotion_layout.addWidget(emotion_label)
        emotion_layout.addWidget(self.emotion_combo, 1)
        
        # 感情強度
        intensity_layout = QHBoxLayout()
        intensity_label = QLabel("感情強度:")
        intensity_label.setMinimumWidth(80)
        
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 200)
        self.intensity_slider.setValue(100)
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
            ("ピッチ", "pitch_scale", 0.5, 1.5, 1.0, "低音 ← → 高音"),
            ("抑揚", "intonation_scale", 0.5, 1.5, 1.0, "平坦 ← → 抑揚"),
            ("SDP比率", "sdp_ratio", 0.0, 0.8, 0.25, "単調 ← → 変化"),
            ("ノイズ", "noise", 0.0, 1.0, 0.35, "クリア ← → 自然")
        ]
        
        self.param_sliders = {}
        self.param_spinboxes = {}
        
        for i, (name, key, min_val, max_val, default, desc) in enumerate(params):
            label = QLabel(name + ":")
            label.setMinimumWidth(80)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(int(min_val * 100), int(max_val * 100))
            slider.setValue(int(default * 100))
            slider.setStyleSheet(self.intensity_slider.styleSheet())
            
            spinbox = QDoubleSpinBox()
            spinbox.setRange(min_val, max_val)
            spinbox.setSingleStep(0.01)
            spinbox.setValue(default)
            spinbox.setDecimals(2)
            spinbox.setFixedWidth(70)
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #666; font-size: 9pt;")
            
            slider.valueChanged.connect(lambda v, k=key: self.on_param_slider_changed(k, v))
            spinbox.valueChanged.connect(lambda v, k=key: self.on_param_spinbox_changed(k, v))
            
            self.param_sliders[key] = slider
            self.param_spinboxes[key] = spinbox
            
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
        
        presets = [
            ("標準", {
                'style': 'Neutral', 'style_weight': 1.0, 'length_scale': 0.85,
                'pitch_scale': 1.0, 'intonation_scale': 1.0, 'sdp_ratio': 0.25, 'noise': 0.35
            }),
            ("高音・速め", {
                'style': 'Happy', 'style_weight': 1.2, 'length_scale': 0.6,
                'pitch_scale': 1.3, 'intonation_scale': 1.2, 'sdp_ratio': 0.4, 'noise': 0.4
            }),
            ("低音・ゆっくり", {
                'style': 'Neutral', 'style_weight': 0.8, 'length_scale': 1.2,
                'pitch_scale': 0.7, 'intonation_scale': 0.8, 'sdp_ratio': 0.15, 'noise': 0.3
            }),
            ("感情豊か", {
                'style': 'Happy', 'style_weight': 1.5, 'length_scale': 0.75,
                'pitch_scale': 1.1, 'intonation_scale': 1.4, 'sdp_ratio': 0.6, 'noise': 0.5
            }),
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
        
        spinbox = self.param_spinboxes[param_key]
        spinbox.blockSignals(True)
        spinbox.setValue(float_value)
        spinbox.blockSignals(False)
        
        self.current_params[param_key] = float_value
        self.emit_parameters_changed()
    
    def on_param_spinbox_changed(self, param_key, value):
        """パラメータ数値入力変更時"""
        int_value = int(value * 100)
        
        slider = self.param_sliders[param_key]
        slider.blockSignals(True)
        slider.setValue(int_value)
        slider.blockSignals(False)
        
        self.current_params[param_key] = value
        self.emit_parameters_changed()
    
    def apply_preset(self, preset_params):
        """プリセットを適用"""
        self.current_params.update(preset_params)
        self.load_parameters()
        self.emit_parameters_changed()
    
    def load_parameters(self):
        """現在のパラメータでUIを更新"""
        self.blockSignals(True)
        
        # 感情
        for i in range(self.emotion_combo.count()):
            if self.emotion_combo.itemData(i) == self.current_params['style']:
                self.emotion_combo.setCurrentIndex(i)
                break
        
        # 感情強度
        style_weight = self.current_params['style_weight']
        self.intensity_slider.setValue(int(style_weight * 100))
        self.intensity_spinbox.setValue(style_weight)
        
        # その他のパラメータ
        for key, value in self.current_params.items():
            if key in self.param_sliders:
                self.param_sliders[key].setValue(int(value * 100))
                self.param_spinboxes[key].setValue(value)
        
        self.blockSignals(False)
    
    def emit_parameters_changed(self):
        """パラメータ変更シグナルを送信"""
        self.parameters_changed.emit(self.row_id, self.current_params.copy())
    
    def get_current_parameters(self):
        """現在のパラメータを取得"""
        return self.current_params.copy()

class TabbedEmotionControl(QWidget):
    """タブ式感情制御ウィジェット"""
    
    parameters_changed = pyqtSignal(str, dict)  # row_id, parameters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.emotion_controls = {}  # row_id -> SingleEmotionControl
        self.init_ui()
        
    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # タブウィジェット（ヘッダーなし）
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e3f2fd;
            }
        """)
        
        layout.addWidget(self.tab_widget)
    
    def add_text_row(self, row_id, row_number, parameters=None):
        """テキスト行に対応するタブを追加"""
        if row_id not in self.emotion_controls:
            control = SingleEmotionControl(row_id, parameters)
            control.parameters_changed.connect(self.parameters_changed)
            
            self.emotion_controls[row_id] = control
            self.tab_widget.addTab(control, str(row_number))
    
    def remove_text_row(self, row_id):
        """テキスト行に対応するタブを削除"""
        if row_id in self.emotion_controls:
            control = self.emotion_controls[row_id]
            index = self.tab_widget.indexOf(control)
            if index != -1:
                self.tab_widget.removeTab(index)
            del self.emotion_controls[row_id]
    
    def update_tab_numbers(self, row_mapping):
        """タブ番号を更新 {row_id: row_number}"""
        for row_id, row_number in row_mapping.items():
            if row_id in self.emotion_controls:
                control = self.emotion_controls[row_id]
                index = self.tab_widget.indexOf(control)
                if index != -1:
                    self.tab_widget.setTabText(index, str(row_number))
    
    def get_parameters(self, row_id):
        """指定行のパラメータを取得"""
        if row_id in self.emotion_controls:
            return self.emotion_controls[row_id].get_current_parameters()
        return {}
    
    def set_current_row(self, row_id):
        """指定行のタブをアクティブに"""
        if row_id in self.emotion_controls:
            control = self.emotion_controls[row_id]
            index = self.tab_widget.indexOf(control)
            if index != -1:
                self.tab_widget.setCurrentIndex(index)