import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class ModelManager:
    def __init__(self, config_file="model_history.json"):
        self.config_file = config_file
        self.models = []
        self.load_history()
    
    def load_history(self):
        """履歴ファイルから読み込み"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.models = data.get('models', [])
                print(f"モデル履歴を読み込み: {len(self.models)}件")
            except Exception as e:
                print(f"履歴読み込みエラー: {e}")
                self.models = []
        else:
            self.models = []
    
    def save_history(self):
        """履歴ファイルに保存"""
        try:
            data = {
                'models': self.models,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("モデル履歴を保存しました")
        except Exception as e:
            print(f"履歴保存エラー: {e}")
    
    def add_model(self, model_path: str, config_path: str, style_path: str, custom_name: str = None) -> str:
        """新しいモデルを履歴に追加"""
        # 既存チェック
        model_id = self._generate_model_id(model_path)
        existing = self.get_model_by_id(model_id)
        
        if existing:
            # 既存の場合は最終使用日時を更新
            existing['last_used'] = datetime.now().isoformat()
            self.save_history()
            return model_id
        
        # 新規追加
        model_name = custom_name or Path(model_path).stem
        
        model_entry = {
            'id': model_id,
            'name': model_name,
            'model_path': model_path,
            'config_path': config_path,
            'style_path': style_path,
            'created_at': datetime.now().isoformat(),
            'last_used': datetime.now().isoformat(),
            'use_count': 1
        }
        
        # 最新を先頭に追加
        self.models.insert(0, model_entry)
        
        # 履歴は最大20件まで
        if len(self.models) > 20:
            self.models = self.models[:20]
        
        self.save_history()
        print(f"モデルを履歴に追加: {model_name}")
        return model_id
    
    def get_model_by_id(self, model_id: str) -> Optional[Dict]:
        """IDでモデル情報を取得"""
        for model in self.models:
            if model['id'] == model_id:
                return model
        return None
    
    def get_all_models(self) -> List[Dict]:
        """全モデル履歴を取得（最新順）"""
        return self.models.copy()
    
    def update_model_name(self, model_id: str, new_name: str) -> bool:
        """モデル名を更新"""
        model = self.get_model_by_id(model_id)
        if model:
            model['name'] = new_name
            self.save_history()
            print(f"モデル名を更新: {new_name}")
            return True
        return False
    
    def update_last_used(self, model_id: str):
        """最終使用日時と使用回数を更新"""
        model = self.get_model_by_id(model_id)
        if model:
            model['last_used'] = datetime.now().isoformat()
            model['use_count'] = model.get('use_count', 0) + 1
            
            # 使用したモデルを先頭に移動
            self.models.remove(model)
            self.models.insert(0, model)
            
            self.save_history()
    
    def remove_model(self, model_id: str) -> bool:
        """モデルを履歴から削除"""
        model = self.get_model_by_id(model_id)
        if model:
            self.models.remove(model)
            self.save_history()
            print(f"モデルを履歴から削除: {model['name']}")
            return True
        return False
    
    def validate_model_files(self, model_entry: Dict) -> bool:
        """モデルファイルの存在確認"""
        paths = [
            model_entry['model_path'],
            model_entry['config_path'],
            model_entry['style_path']
        ]
        
        for path in paths:
            if not os.path.exists(path):
                return False
        return True
    
    def _generate_model_id(self, model_path: str) -> str:
        """モデルパスからユニークIDを生成"""
        import hashlib
        return hashlib.md5(model_path.encode()).hexdigest()[:12]
    
    def get_formatted_datetime(self, iso_string: str) -> str:
        """日時を見やすい形式に変換"""
        try:
            dt = datetime.fromisoformat(iso_string)
            now = datetime.now()
            diff = now - dt
            
            if diff.days == 0:
                if diff.seconds < 3600:  # 1時間以内
                    minutes = diff.seconds // 60
                    return f"{minutes}分前"
                else:  # 1時間以上、1日以内
                    hours = diff.seconds // 3600
                    return f"{hours}時間前"
            elif diff.days == 1:
                return "昨日"
            elif diff.days < 7:
                return f"{diff.days}日前"
            else:
                return dt.strftime("%m/%d")
        except:
            return "不明"