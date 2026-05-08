# ComfyUI-Manager セキュリティレベルエラーの解消

ComfyUI-Manager からカスタムノードをインストールしようとすると、以下のようなエラーで失敗する場合の対処手順。

```
[Installation Errors]
'ComfyUI_IPAdapter_plus': This action is not allowed with this security level configuration.
```

## 原因

本リポジトリは ComfyUI を **v0.3.60** に pin している（gfx906 / ROCm 5.7 の都合。詳しくは [README の該当節](README.md#comfyui-を-v0360-に-pin-している理由)）。

一方、新しい ComfyUI-Manager は ComfyUI 本体側の **System User Protection API**（PR #10966、ComfyUI v0.3.70 以降に存在）を前提としており、この API が無い古い ComfyUI で `--listen 0.0.0.0` 起動している場合、**`config.ini` の値を無視して `security_level = 'strong'` に強制上書き** する仕様になっている（`glob/manager_migration.py` の `force_security_level_if_needed` 関数）。

そのため:

- `config.ini` で `security_level = weak` にしても効かない
- v0.3.60 を使う限り API は提供されないので、**Manager 側にもパッチが必要**

## 修正手順

### 1. `config.ini` の `security_level` を `weak` に変更

ファイル: `~/comfyui-data/user/default/ComfyUI-Manager/config.ini`

```ini
security_level = weak
```

このファイルはコンテナ内の root が作成するため、ホスト側からの編集には sudo が必要。一括書き換えなら:

```bash
sudo sed -i 's/^security_level = strong$/security_level = weak/' \
  ~/comfyui-data/user/default/ComfyUI-Manager/config.ini
```

### 2. ComfyUI-Manager の強制上書きを無効化

ファイル: `~/comfyui-data/custom_nodes/ComfyUI-Manager/glob/manager_migration.py`

`force_security_level_if_needed` 関数の中身を、**何もしない（常に `False` を返す）** に書き換える:

```python
def force_security_level_if_needed(config_dict):
    """Force security level to 'strong' if on old ComfyUI."""
    # PATCHED: ComfyUI is pinned to v0.3.60 (gfx906/ROCm5.7), which lacks the
    # System User Protection API (PR #10966). Without this patch, Manager
    # forces security_level='strong' regardless of config.ini.
    return False
```

### 3. コンテナ再起動

```bash
cd ~/comfyui-data
sudo docker compose restart
```

これで Manager から任意のソースのカスタムノードをインストールできるようになる。

## 注意事項

- **ComfyUI-Manager をアップデートすると `manager_migration.py` のパッチは消える**。アップデート後は同じ修正を再適用する
- `security_level = weak` は「任意のソースのプラグインインストールを許可」する設定。LAN に信頼できないユーザーがいる環境では、必要なインストール作業が終わったら `normal` に戻すのが安全:

  ```bash
  sudo sed -i 's/^security_level = weak$/security_level = normal/' \
    ~/comfyui-data/user/default/ComfyUI-Manager/config.ini
  sudo docker compose restart
  ```

  ただし `normal` 以上に戻すとリモート（LAN 経由）アクセスからの Manager 操作が再びブロックされるため、運用ポリシーと合わせて選択する

## 参考

- ComfyUI-Manager の security policy: <https://github.com/ltdrdata/ComfyUI-Manager#security-policy>
- 解説記事（日本語）: <https://comfyui-wiki.com/ja/faq/fix-comfyui-manager-security-level-error>
