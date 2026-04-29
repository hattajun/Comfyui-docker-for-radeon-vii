---
name: Bug report
about: 動作不具合の報告
title: '[bug] '
labels: bug
---

## 症状

何が起きたか・期待した動作との差を簡潔に。

## 再現手順

1.
2.
3.

## 環境

- GPU: <!-- 例: AMD Radeon VII / Radeon Pro VII -->
- OS: <!-- 例: Ubuntu 24.04 LTS -->
- カーネル: <!-- 例: 6.8.0-xx -->
- amdgpu ドライバ: <!-- 例: kernel 同梱 / 別途インストール -->
- Docker: <!-- `docker --version` の結果 -->
- このリポジトリのコミット: <!-- `git rev-parse HEAD` の結果 -->
- ベースモデル: <!-- 例: sd_xl_base_1.0.safetensors / ace_step_v1_3.5b.safetensors -->

## ComfyUI ログ

```
コンテナのログ最後 30 行程度を貼り付け（docker compose logs --tail 30 comfyui-rocm57）
```

## 試したこと

- [ ] README のトラブルシューティングを確認
- [ ] `docker compose down && docker compose up -d` で再起動した
- [ ] `~/comfyui-data/` 内のファイル権限を確認
- [ ] その他: <!-- 自由記述 -->

## 補足

スクリーンショット・関連 URL 等あれば。
