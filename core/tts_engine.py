import torch
import numpy as np
from pathlib import Path
import traceback
import inspect
import logging

# Style-Bert-VITS2のログを無効化
logging.getLogger("style_bert_vits2").setLevel(logging.ERROR)
logging.getLogger("bert_models").setLevel(logging.ERROR)  
logging.getLogger("tts_model").setLevel(logging.ERROR)
logging.getLogger("infer").setLevel(logging.ERROR)

# 他の一般的なログも必要に応じて無効化
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)

class TTSEngine:
    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.model_info = {}
        
        # デフォルトパラメータ
        self.default_params = {
            'style': 'Neutral',
            'style_weight': 1.0,
            'sdp_ratio': 0.25,
            'noise': 0.35,
            'length_scale': 0.85
        }
        
    def load_model(self, model_path, config_path, style_path):
        """モデルを読み込む"""
        try:
            # BERTモデルの読み込み
            from style_bert_vits2.nlp import bert_models
            from style_bert_vits2.constants import Languages
            from style_bert_vits2.tts_model import TTSModel
            
            bert_models.load_model(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
            bert_models.load_tokenizer(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
            
            # TTSモデル読み込み
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self.model = TTSModel(
                model_path=model_path,
                config_path=config_path,
                style_vec_path=style_path,
                device=device,
            )
            
            # モデル情報を保存
            self.model_info = {
                'model_path': model_path,
                'config_path': config_path,
                'style_path': style_path,
                'device': device
            }
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            self.is_loaded = False
            return False
    
    def get_available_styles(self):
        """利用可能な感情スタイルを取得"""
        if not self.is_loaded or not self.model:
            return ["Neutral"]
        
        # モデルから実際の感情リストを取得を試みる
        try:
            # config.jsonから感情情報を取得
            import json
            with open(self.model_info.get('config_path', ''), 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 学習済み感情を確認
            if 'data' in config and 'emotions' in config['data']:
                emotions = config['data']['emotions']
                return emotions
            elif 'emotions' in config:
                emotions = config['emotions']
                return emotions
            else:
                pass
        except Exception as e:
            pass
        # デフォルト（一般的な感情リスト）
        return [
            "Neutral",
            "Happy", 
            "Sad",
            "Angry",
            "Fear",
            "Disgust",
            "Surprise"
        ]
    
    def synthesize(self, text, **params):
        """音声合成を実行"""
        if not self.is_loaded or self.model is None:
            raise RuntimeError("モデルが読み込まれていません")
        
        if not text.strip():
            raise ValueError("テキストが空です")
            
        try:
            # パラメータを準備
            synth_params = self.default_params.copy()
            synth_params.update(params)
                        
            # モデルの infer メソッドのシグネチャを確認して安全に呼び出し
            kwargs = self._build_infer_kwargs(text, synth_params)
            
            # 音声合成実行
            sr, audio = self.model.infer(**kwargs)
            
            # 結果チェック
            if audio is None or len(audio) == 0:
                raise RuntimeError("音声データが生成されませんでした")
                
            return sr, audio
            
        except Exception as e:
            raise e
    
    def _build_infer_kwargs(self, text, params):
        """infer() メソッドに渡す引数を安全に構築"""
        if not self.model:
            raise RuntimeError("モデルが読み込まれていません")
            
        # メソッドシグネチャを取得
        sig = inspect.signature(self.model.infer)
        method_params = sig.parameters
        
        # テキスト引数
        kwargs = {}
        if "text" in method_params:
            kwargs["text"] = text
        else:
            # 最初の位置引数にテキストを設定
            first_param = next(iter(method_params))
            kwargs[first_param] = text
        
        # スタイル系
        if "style" in method_params:
            kwargs["style"] = params.get('style', 'Neutral')

        if "style_weight" in method_params:
            kwargs["style_weight"] = params.get('style_weight', 1.0)
        elif "emotion_weight" in method_params:
            kwargs["emotion_weight"] = params.get('style_weight', 1.0)

        # 長さ系（複数のパラメータ名をチェック）
        length_scale = params.get('length_scale', 0.85)
        
        if "length_scale" in method_params:
            kwargs["length_scale"] = length_scale
        elif "duration_scale" in method_params:
            kwargs["duration_scale"] = length_scale
            # speedの場合は逆数になることが多い
            speed_value = 1.0 / length_scale
            kwargs["speed"] = speed_value
        elif "length" in method_params:
            kwargs["length"] = length_scale
        else:
            pass
        # SDP
        sdp_value = params.get('sdp_ratio', 0.25)
        
        if "sdp_ratio" in method_params:
            kwargs["sdp_ratio"] = sdp_value
        elif "sdp" in method_params:
            kwargs["sdp"] = sdp_value  
        else:
            pass
        # ノイズ系（優先順位: noise > noise_scale_w > noise_scale）
        noise_value = params.get('noise', 0.35)
        
        if "noise" in method_params:
            kwargs["noise"] = noise_value
        elif "noise_scale_w" in method_params:
            kwargs["noise_scale_w"] = noise_value
        elif "noise_scale" in method_params:
            kwargs["noise_scale"] = noise_value
        else:
            pass
        # ピッチとイントネーション（新発見！）
        if "pitch_scale" in method_params:
            pitch_value = params.get('pitch_scale', 1.0)
            kwargs["pitch_scale"] = pitch_value
        
        if "intonation_scale" in method_params:
            intonation_value = params.get('intonation_scale', 1.0)
            kwargs["intonation_scale"] = intonation_value
        
        return kwargs
    
    def get_model_info(self):
        """モデル情報を取得"""
        return self.model_info.copy() if self.is_loaded else {}
    
    def unload_model(self):
        """モデルをアンロード"""
        if self.model:
            del self.model
            self.model = None
        self.is_loaded = False
        self.model_info = {}
        
        # GPU メモリをクリア
        if torch.cuda.is_available():
            torch.cuda.empty_cache()