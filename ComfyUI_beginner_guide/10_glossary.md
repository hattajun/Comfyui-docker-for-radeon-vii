# 付録：用語集

> 各用語の右に **「初出: 第N章」** のリンクを併記しています。文脈を確認したいときにジャンプしてください。

## ComfyUI の基本用語

### ノード (Node) — [初出: 第1章](01_introduction.md)
ワークフローを構成する1つの箱。「モデルを読み込む」「テキストを変換する」など、1つの仕事を担当する。

### ワイヤー (Wire) — [初出: 第1章](01_introduction.md)
ノード同士をつなぐ線。前のノードの出力を次のノードの入力に渡す。**色** が型を表す（同じ色のソケット同士しかつなげない）。

### ワークフロー (Workflow) — [初出: 第1章](01_introduction.md)
ノードとワイヤーで組まれた一連の処理の図。`.json` ファイルとして保存・共有できる。

### キャンバス — [初出: 第2章](02_ui_tour.md)
ワークフローを並べる広い作業領域。マウスホイールでズーム、右クリックドラッグで移動。

### キュー (Queue) — [初出: 第2章](02_ui_tour.md)
実行待ちのジョブの行列。`実行する` を押すたびにキューに追加される。

### テンプレート (Template) — [初出: 第2章](02_ui_tour.md)
ComfyUI 公式が用意した出来合いのワークフロー。Stable Audio や ACE-Step などはここから開く。

### バイパス (Bypass) — [初出: 第8章](08_ace_step.md)
ノードを「実行スキップ状態」にすること。半透明で表示される。右クリック → Bypass で切替。

---

## モデル関連

### チェックポイント / Checkpoint — [初出: 第3章](03_setup.md)
画像や音楽を生成する **AI の本体** ファイル。一番大きい（4〜10GB）。`models/checkpoints/` に置く。

### CLIP / Text Encoder — [初出: 第7章](07_stable_audio.md)
**テキスト（プロンプト）を AI が理解できる数値ベクトルに変換** するモデル。SDXL は内部に持っているので別ファイル不要だが、Stable Audio は `t5-base.safetensors` を別途必要とする。

### VAE — [初出: 第4章](04_image_generation.md)
**Latent（潜在空間）と Pixel（実際の画像）を相互変換** するモデル。多くのチェックポイントには内蔵されている。

### LoRA
チェックポイントに対する **微調整パッチ**。ファイルが小さい（数十〜数百MB）。特定のキャラクター、画風、ジャンルを足したい時に使う。`models/loras/` に置く。本ガイドでは未使用。

### ControlNet
**構図を画像で指定** するためのモデル（線画 → 同じポーズの画像、など）。`models/controlnet/` に置く。本ガイドでは未使用。

### Embedding
プロンプトの一部として使える **学習済みの単語ベクトル**。`models/embeddings/` に置く。本ガイドでは未使用。

---

## 生成プロセス関連

### 拡散プロセス (Diffusion Process) — [初出: 第4章](04_image_generation.md)
ノイズだらけの状態から、徐々にノイズを取り除いていって意味のある画像/音にする AI の動作原理。

### Latent / 潜在空間 — [初出: 第4章](04_image_generation.md)
拡散プロセスが行われる **数値だけの内部表現**。VAE で人間の見える形に戻して初めて使える。

### KSampler / Kサンプラー — [初出: 第2章](02_ui_tour.md)
拡散プロセスを実行する **中心ノード**。シード、ステップ数、cfg、サンプラー名などを設定する。

### シード (Seed) — [初出: 第4章](04_image_generation.md)
乱数の初期値。**同じシード + 同じプロンプト + 同じ設定** なら毎回同じ結果が出る。

### ステップ (Steps) — [初出: 第4章](04_image_generation.md)
ノイズ除去を **何回繰り返すか**。多いほど密度が増すが、時間がかかる。

### CFG (Classifier-Free Guidance) — [初出: 第4章](04_image_generation.md)
**プロンプトをどれだけ重視するか** の倍率。高いほどプロンプト忠実、下げるほど AI の自由度が上がる。SDXL は 6〜8、Stable Audio は 4〜7、ACE-Step は 5 が目安。

### サンプラー (Sampler) — [初出: 第4章](04_image_generation.md)
**ノイズ除去のアルゴリズム**。`euler`、`dpmpp_2m`、`dpmpp_3m_sde_gpu` などがある。モデルによって相性がある。

### スケジューラ (Scheduler) — [初出: 第4章](04_image_generation.md)
**ステップごとのノイズ量の配分** を決める。`normal`、`karras`、`exponential`、`simple` など。

### ノイズ除去 (Denoise) — [初出: 第4章](04_image_generation.md)
1.0 で「全ノイズを除去」、0.5 で「半分だけ除去」。Image-to-Image 等で 1.0 未満を使う。

---

## モデル別の用語

### SDXL
Stable Diffusion XL の略。**画像生成** モデル。デフォルトの解像度は 1024×1024。本ガイドの第4章で使用。

### Stable Audio Open 1.0
Stability AI が公開した **音声生成** モデル。最大 47.6 秒、効果音や短い音楽が得意。本ガイドの第7章で使用。

### ACE-Step v1
Comfy-Org が再パッケージした **音楽生成** モデル。3.5B パラメータ、最大4分弱、ボーカル対応、多言語対応。本ガイドの第8章で使用。

### T5
Google が公開したテキスト変換モデル。Stable Audio がプロンプトを理解するために使う。`text_encoders/t5-base.safetensors` として配置。

---

## ファイル形式

| 拡張子 | 中身 |
|---|---|
| `.safetensors` | 安全な形式の AI モデル重み（推奨） |
| `.ckpt` | 古い形式のモデル重み（PyTorch pickle） |
| `.pt` `.pth` | PyTorch のチェックポイント |
| `.json` | ComfyUI のワークフロー定義 |
| `.png` | 出力画像。ComfyUI はここに **ワークフロー JSON を埋め込む** ので、PNG をキャンバスにドラッグ&ドロップで復元できる |
| `.flac` | 可逆圧縮の音声形式（Stable Audio のデフォルト出力） |
| `.mp3` | 圧縮音声形式（ACE-Step のデフォルト出力） |
| `.opus` | 圧縮音声形式（ACE-Step の追加出力、Bypass 解除で有効化） |

---

## ハードウェア用語

### VRAM
GPU の専用メモリ。AI 生成では **6GB 以上** が現実的、**12GB 以上** で快適。本ガイドの環境は 16GB（AMD Radeon VII）。

### CUDA / ROCm
GPU 計算用のフレームワーク。**CUDA = NVIDIA**、**ROCm = AMD**。ComfyUI はどちらも対応。

### バッチ (Batch)
1度の実行で生成する個数。バッチサイズ 4 = 4枚同時生成。VRAM 消費が増える。

---

## トラブル時に出る用語

| 用語 | 意味 |
|---|---|
| `out of memory` | VRAM 不足 |
| `RuntimeError: CUDA error` | GPU 計算で何か失敗 |
| `KeyError` | 必要なキー（モデル名、ノード名）が存在しない |
| `Stack trace` | エラーが発生した場所までの呼び出し履歴 |
| `Bypass` | ノードを実行スキップ状態にすること |

---

## 参考リンク

- [ComfyUI 公式 GitHub](https://github.com/comfyanonymous/ComfyUI)
- [Comfy-Org の Hugging Face](https://huggingface.co/Comfy-Org)（再パッケージ済みモデル）
- [r/comfyui (Reddit)](https://www.reddit.com/r/comfyui/)
- [ComfyUI Examples](https://comfyanonymous.github.io/ComfyUI_examples/)（公式ワークフローの解説）

---

[← 目次に戻る](00_index.md)
