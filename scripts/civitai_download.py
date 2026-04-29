#!/usr/bin/env python3
"""
Civitai のモデルを ~/comfyui-data/models/{type}/ に保存する CLI。

使い方:
    # 単発（モデルページ URL から）
    ./civitai_download.py https://civitai.com/models/123456
    ./civitai_download.py https://civitai.com/models/123456?modelVersionId=789012
    ./civitai_download.py 789012   # version ID 直接指定

    # マニフェスト（複数 URL を一括）
    ./civitai_download.py --manifest models.txt

    # 出力先のルート（既定 ~/comfyui-data/models）
    ./civitai_download.py --root /custom/path URL

API key（必要な場合）:
    https://civitai.com/user/account でトークンを発行
    環境変数 CIVITAI_TOKEN にセットすると自動で使われる。

依存: Python 標準ライブラリのみ（requests 不要）。

License: MIT (see LICENSE in repository root)
Repository: https://github.com/hattajun/Comfyui-docker-for-radeon-vii
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://civitai.com/api/v1"
DOWNLOAD_BASE = "https://civitai.com/api/download/models"

# Civitai の type → ComfyUI 配下のサブディレクトリ
TYPE_TO_DIR = {
    "Checkpoint": "checkpoints",
    "LORA": "loras",
    "LoCon": "loras",
    "DoRA": "loras",
    "TextualInversion": "embeddings",
    "Hypernetwork": "hypernetworks",
    "VAE": "vae",
    "Controlnet": "controlnet",
    "Upscaler": "upscale_models",
    "MotionModule": "animatediff_models",
    "Other": "other",
}


def auth_headers() -> dict:
    """User-Agent と必要なら Bearer Token。"""
    h = {"User-Agent": "civitai-dl/1.0 (+local-script)"}
    token = os.environ.get("CIVITAI_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=auth_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_arg(arg: str) -> tuple[int | None, int | None]:
    """ユーザー入力 → (model_id, version_id)。両方 None の入力は不正。"""
    # 数字だけなら version_id とみなす
    if arg.isdigit():
        return None, int(arg)
    # URL パース
    m = re.match(r"https?://civitai\.com/models/(\d+)", arg)
    if not m:
        raise ValueError(f"認識できない入力: {arg!r}")
    model_id = int(m.group(1))
    version_id = None
    qs = urllib.parse.urlparse(arg).query
    for k, v in urllib.parse.parse_qsl(qs):
        if k == "modelVersionId":
            version_id = int(v)
            break
    return model_id, version_id


def resolve_version(model_id: int | None, version_id: int | None) -> dict:
    """version_id を使って model-versions API からメタ情報取得。
    version_id が無ければ model API で latest version を選ぶ。"""
    if version_id is None:
        if model_id is None:
            raise ValueError("model_id も version_id も指定なし")
        m = get_json(f"{API_BASE}/models/{model_id}")
        versions = m.get("modelVersions") or []
        if not versions:
            raise RuntimeError(f"model {model_id} に version が見つからない")
        # 配列の先頭が最新（API 仕様）
        version_id = versions[0]["id"]
    return get_json(f"{API_BASE}/model-versions/{version_id}")


def pick_primary_file(version: dict) -> dict:
    """versions['files'] からプライマリファイル（重みファイル）を選ぶ。"""
    files = version.get("files") or []
    if not files:
        raise RuntimeError("ファイルが空")
    # primary フラグがあるものを優先、無ければ最大サイズ（通常は重み本体）
    for f in files:
        if f.get("primary"):
            return f
    return max(files, key=lambda f: f.get("sizeKB", 0))


def download(url: str, dest: Path) -> None:
    """resume なし、進捗表示付きの単純 DL。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers=auth_headers())
    with urllib.request.urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk = 1024 * 1024  # 1 MiB
        with open(tmp, "wb") as out:
            while True:
                buf = resp.read(chunk)
                if not buf:
                    break
                out.write(buf)
                downloaded += len(buf)
                if total:
                    pct = downloaded * 100 / total
                    bars = int(pct / 2)
                    print(
                        f"\r  [{'='*bars}{' '*(50-bars)}] {pct:5.1f}% "
                        f"({downloaded/1024/1024:.0f} / {total/1024/1024:.0f} MiB)",
                        end="", flush=True,
                    )
        print()
    tmp.rename(dest)


def fetch_one(arg: str, root: Path) -> None:
    print(f"\n=== {arg} ===")
    try:
        model_id, version_id = parse_arg(arg)
        version = resolve_version(model_id, version_id)
    except Exception as e:
        print(f"  解決失敗: {e}", file=sys.stderr)
        return

    primary = pick_primary_file(version)
    filename = primary["name"]
    size_mb = primary.get("sizeKB", 0) / 1024
    model_type = version.get("model", {}).get("type", "Other")
    sub = TYPE_TO_DIR.get(model_type, "other")

    print(f"  model:    {version.get('model', {}).get('name')!r} ({model_type})")
    print(f"  version:  {version.get('name')!r} (id={version['id']})")
    print(f"  file:     {filename} ({size_mb:.1f} MiB)")
    print(f"  type→dir: {model_type} → models/{sub}/")

    dest = root / sub / filename
    if dest.exists():
        existing_mb = dest.stat().st_size / 1024 / 1024
        if size_mb and abs(existing_mb - size_mb) < 1:
            print(f"  既に存在（{existing_mb:.1f} MiB）→ スキップ")
            return
        print(f"  既存ファイル {existing_mb:.1f} MiB がサイズ違いで上書き")

    dl_url = f"{DOWNLOAD_BASE}/{version['id']}"
    if "CIVITAI_TOKEN" in os.environ:
        dl_url += f"?token={os.environ['CIVITAI_TOKEN']}"
    print(f"  → {dest}")
    download(dl_url, dest)
    print(f"  ✓ 完了")


def main() -> int:
    p = argparse.ArgumentParser(description="Civitai のモデルを DL")
    p.add_argument("urls", nargs="*", help="モデルページ URL または version ID")
    p.add_argument("--manifest", help="1行1URL のテキストファイル")
    p.add_argument(
        "--root", default=str(Path.home() / "comfyui-data" / "models"),
        help="保存ルート（既定: ~/comfyui-data/models）",
    )
    args = p.parse_args()

    targets: list[str] = list(args.urls)
    if args.manifest:
        with open(args.manifest, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    targets.append(line)

    if not targets:
        p.print_usage(sys.stderr)
        return 2

    root = Path(args.root).expanduser()
    print(f"DL root: {root}")
    if "CIVITAI_TOKEN" not in os.environ:
        print("(注: CIVITAI_TOKEN 未設定。NSFW フラグや認証必須モデルは失敗します)")

    for t in targets:
        try:
            fetch_one(t, root)
        except KeyboardInterrupt:
            print("\n中断", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"  失敗: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
