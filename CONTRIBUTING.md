# Contributing

このリポジトリへの contribution を歓迎します。

## 想定する貢献の種類

- ドキュメントの誤字脱字・分かりにくい説明の改善
- 他の AMD GPU（gfx906 以外の Vega 系等）での動作報告
- ROCm / PyTorch 新バージョンとの互換性検証結果
- ComfyUI 新バージョンに pin を上げる試み（gfx906 互換が壊れない範囲で）
- トラブルシューティングセクションへの追記
- Civitai 取得スクリプトの機能拡張・バグ修正
- 英語版ドキュメントの翻訳

## 始め方

1. Issue で **やりたいことを書く**（重複や方向性のすり合わせ）
2. Fork して branch 作成
3. 変更
4. PR を出す（小さく分割推奨）

## ドキュメントスタイル

- 既存の章に合わせ **「初心者目線」を保つ**（前提知識を仮定しすぎない）
- スクリーンショットを追加する場合は `ComfyUI_beginner_guide/screenshots/` に置き、md 内で相対パスで参照
- 用語は [10_glossary.md](ComfyUI_beginner_guide/10_glossary.md) に登録 or 既存の用語に揃える

## コードスタイル（scripts/）

- Python 標準ライブラリのみで完結させる方針（pip 依存を増やさない）
- 既存の `civitai_download.py` のスタイル（型ヒント・docstring の長さ等）に合わせる

## 動作確認した環境を Issue / PR で必ず書いてください

特にハード絡みの話は **GPU 型番・ROCm バージョン・OS** が分かると再現しやすいです。
[Issue テンプレート](.github/ISSUE_TEMPLATE/bug_report.md) を使うと記入漏れが減ります。

## ライセンス

contribute すると、本リポジトリの [MIT License](LICENSE) で配布されることに同意したものとみなします。
