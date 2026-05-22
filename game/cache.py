import hashlib
import json
import os
import urllib.parse

try:
    import renpy
except ImportError:
    renpy = None


class CacheManager:
    """Simple file cache for Atlas Academy downloads."""

    def __init__(self):
        if renpy is not None:
            game_dir = renpy.config.gamedir
        else:
            game_dir = os.path.dirname(__file__)

        self.base_dir = os.path.join(game_dir, "cache", "atlas_academy")
        self.json_dir = os.path.join(self.base_dir, "json")
        self.text_dir = os.path.join(self.base_dir, "text")
        self.asset_dir = os.path.join(self.base_dir, "asset")

        for directory in (self.base_dir, self.json_dir, self.text_dir, self.asset_dir):
            os.makedirs(directory, exist_ok=True)

    def _hashed_name(self, url: str, ext: str) -> str:
        # Atlas URLs can contain slashes and query strings, so cache by stable hash.
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return f"{digest}{ext}"

    def _file_path(self, url: str, directory: str, ext: str) -> str:
        return os.path.join(directory, self._hashed_name(url, ext))

    def load_json(self, url: str):
        path = self._file_path(url, self.json_dir, ".json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception:
            return None

    def save_json(self, url: str, data) -> None:
        path = self._file_path(url, self.json_dir, ".json")
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)

    def load_text(self, url: str):
        path = self._file_path(url, self.text_dir, ".txt")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return fp.read()
        except Exception:
            return None

    def save_text(self, url: str, text: str) -> None:
        path = self._file_path(url, self.text_dir, ".txt")
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)

    def get_asset_path(self, url: str):
        parsed = urllib.parse.urlparse(url)
        ext = os.path.splitext(parsed.path)[1] or ".bin"
        path = self._file_path(url, self.asset_dir, ext)
        return path if os.path.exists(path) else None

    def save_asset(self, url: str, content: bytes):
        parsed = urllib.parse.urlparse(url)
        ext = os.path.splitext(parsed.path)[1] or ".bin"
        path = self._file_path(url, self.asset_dir, ext)
        with open(path, "wb") as fp:
            fp.write(content)
        return path
