# ComfyUI on Radeon VII (gfx906) — Docker setup

> 🇯🇵 **Documentation is in Japanese.** PRs welcoming an English translation are welcome.

Radeon VII (Vega 20, gfx906) で [ComfyUI](https://github.com/comfyanonymous/ComfyUI) を Docker から動かすセットアップ。SDXL 1024×1024 を ~28秒/枚で生成可能。

ROCm 6.x で gfx906 が deprecated になったため、ROCm 5.7 を Docker で隔離した構成にしている（ホストの新しい ROCm/ドライバを汚さない）。

> 📁 本書では永続データ用ディレクトリとして `~/comfyui-data/` を例として使います。お使いの環境に合わせて読み替えてください。

## 前提

- Ubuntu 24.04 LTS（他の最近の Linux でも動く可能性は高い）
- Radeon VII (Vega 20)
- ホストに `amdgpu` カーネルドライバ（標準カーネルに同梱）
- Docker 20.10 以降（GPU passthrough 可）

## 動作確認済み環境

- ハードウェア: AMD Radeon VII (16 GB HBM2)
- Driver: Linux kernel 同梱の amdgpu
- ROCm in container: 5.7
- PyTorch: 2.3.1+rocm5.7
- ComfyUI: v0.3.60 (pin)
- ベンチ: SDXL base 1.0、1024×1024、20 step、euler、cfg 7.5
  - コールドスタート: 44s
  - ウォーム: **28s/枚**
  - VRAM 使用: 9.5 GB / 16 GB

## 互換性（他の Vega 系 GPU について）

> ⚠️ **以下は理論的な互換性情報で、実動作は未確認です。** 本リポジトリは Radeon VII (gfx906) のみで動作実績があります。下記の差分案を試した方の動作報告を [Issue](.github/ISSUE_TEMPLATE/bug_report.md) でいただけると助かります。

### アーキテクチャ早見表

| GPU | アーキ | gfx ID | 本構成での動作 |
|-----|------|------|------|
| Radeon VII / Radeon Pro VII | Vega 20 | `gfx906` | ✅ 動作確認済み（本リポジトリの想定） |
| Radeon RX Vega 56 / 64 | Vega 10 | `gfx900` | ⚠️ 後述の差分で動く可能性大、未検証 |
| Ryzen APU 内蔵 Vega (Picasso, Renoir 等) | Vega iGPU | `gfx902` / `gfx90c` | ❌ 推奨しない |

### Vega 56 / 64 (gfx900) で動かす場合の差分（未検証）

本リポジトリは Radeon VII (gfx906) 向けに `HSA_OVERRIDE` 等を設定しています。Vega 10 系で試す場合は **2 箇所** 書き換えが必要:

```dockerfile
# Dockerfile（最後の ENV 2 行を変更）
ENV HSA_OVERRIDE_GFX_VERSION=9.0.0   # gfx900 用（現状 9.0.6）
ENV PYTORCH_ROCM_ARCH=gfx900         # （現状 gfx906）
```

```yaml
# docker-compose.yml の environment セクションも同様に
environment:
  HSA_OVERRIDE_GFX_VERSION: "9.0.0"
  PYTORCH_ROCM_ARCH: "gfx900"
```

加えて検討すべき点:

- **VRAM 8GB の制約**:
  - SD 1.5 (512×512): 余裕（推奨）
  - SDXL (1024×1024): フル設定だと OOM、`--lowvram` / `--medvram` フラグ必須、生成時間も伸びる
  - Flux: 事実上動かないと考えてよい
- **HBM2 帯域は Radeon VII (1024 GB/s) より低い (483 GB/s)** ので、SD 1.5 で多少遅め程度に収まるはず
- **gfx900 は ROCm 4.5 で公式 deprecated**（gfx906 よりも早期）。本構成の ROCm 5.7 では認識自体は可能だが不安定要素は gfx906 より多い
- 起動後に `docker logs` で `AMD arch: gfx900` と出るか確認

### Vega APU (gfx902 / gfx90c) について（未検証、非推奨）

**理屈上は可能だが実用的には厳しい**:

- iGPU は **システム RAM を共有**。BIOS で UMA Buffer を最大 8GB に設定しても、実質速度は dGPU の 1/10 以下が想定される
- ROCm の APU サポートは公式に「サポート」と謳われた時期がほぼ無く、動いた事例はあるが品質保証なし
- 現実的な代替案:
  - ComfyUI を `--cpu` フラグで完全 CPU モードで起動する（遅いが確実）
  - SD 1.5 + Q4 量子化 + 解像度小さめ なら数分/枚レベルで生成できることも
  - SDXL は事実上不可

Vega APU しかない環境では、**CPU モードで割り切る** か、外付け GPU の追加を検討するのが現実的です。

### その他の GPU について（参考）

本リポジトリ構成 (ROCm 5.7 + ComfyUI v0.3.60 pin) は gfx906 周辺を念頭にしているため、以下は **このリポジトリではなく上流の最新 ROCm/ComfyUI を直接使うほうが筋が良い** です:

| GPU | 推奨パス |
|-----|---------|
| RDNA1 (RX 5000 系, gfx1010) | ROCm 5.x で部分対応、別レシピが必要 |
| RDNA2 (RX 6000 系) | ROCm 6.x で公式サポート、最新 ComfyUI を直接使える |
| RDNA3 (RX 7000 系) | 同上、最新 ROCm を素直に使う |

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `Dockerfile` | ROCm 5.7 + PyTorch + ComfyUI v0.3.60 のイメージ定義 |
| `docker-compose.yml` | コンテナ起動設定のサンプル（GPU passthrough・ボリューム・port 等） |
| `scripts/civitai_download.py` | Civitai モデルの自動 DL CLI |
| `scripts/models.txt.example` | バッチ DL 用マニフェストの雛形 |
| `ComfyUI_beginner_guide/` | 初心者向け操作ガイド（画像・音楽生成） |
| `LICENSE` | MIT License |

## セットアップ手順

### 1. 事前確認

```bash
# Radeon VII が認識されているか
lspci | grep -i 'amd.*vega'

# /dev/dri と /dev/kfd がある（kfd = ROCm カーネル driver）
ls /dev/dri/
ls /dev/kfd

# どの /dev/dri/renderDxxx が Radeon VII か確認（最も確実な方法）
ls -l /dev/dri/by-path/
```

`by-path` は PCI アドレスと render node のシンボリックリンクで、出力例:

```
pci-0000:0a:00.0-card   -> ../card1
pci-0000:0a:00.0-render -> ../renderD128   ← この renderD の番号を docker-compose.yml に書く
```

PCI アドレスが Radeon VII (Vega 20) のものか `lspci` の結果と突き合わせて確認してください。

**`docker-compose.yml` のデフォルトは `/dev/dri/renderD128`** にしてあります（単独 GPU 環境ではほぼこの番号）。NVIDIA 等の他 GPU と共存して **Radeon VII の PCI アドレスが他より大きい場合は `renderD129` 等にずれる**ので、上記手順で確認して書き換えてください。

### 2. Docker のインストール（既にあればスキップ）

公式リポジトリから:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
# 反映: 一度ログアウト→ログイン or `newgrp docker`
```

### 3. このリポジトリを clone

```bash
git clone https://github.com/hattajun/Comfyui-docker-for-radeon-vii.git
cd Comfyui-docker-for-radeon-vii
```

### 4. 永続データ用ディレクトリ準備

モデル・出力・カスタムノードはホスト側に保存する:

```bash
mkdir -p ~/comfyui-data/{models/{checkpoints,vae,loras,clip,clip_vision,controlnet,embeddings,upscale_models,text_encoders},output,custom_nodes,user,input}
```

### 5. ビルド（リポジトリのルートで実行）

初回 ~5-10 分（PyTorch 2.3.1+rocm5.7 wheel ~5GB を pull）:

```bash
docker build -t comfyui-rocm57:latest .
```

ビルド完了後、イメージは Docker のローカルレジストリに `comfyui-rocm57:latest` として登録される。以降この tag をどこからでも参照できる。

### 6. compose ファイルを永続データ側にコピー

ボリュームの相対パス (`./models` 等) を解決させるため、compose だけ `~/comfyui-data/` 配下に置く:

```bash
cp docker-compose.yml ~/comfyui-data/docker-compose.yml
```

複数 GPU 環境で `/dev/dri/renderD128` の番号がずれる場合はここで編集する（事前確認で得た番号に合わせる）。

### 7. SDXL ベースモデル取得

```bash
wget -O ~/comfyui-data/models/checkpoints/sd_xl_base_1.0.safetensors \
  https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
```

Civitai のモデルは付属スクリプトで取得できる（[後述](#civitai-モデルの取得付属スクリプト)）。他は [Hugging Face](https://huggingface.co/) から `.safetensors` を `models/checkpoints/` 等に置けば自動認識される。

### 8. 起動

```bash
cd ~/comfyui-data
docker compose up -d
docker compose logs -f         # ログ確認
```

ブラウザで `http://localhost:8188` を開けば ComfyUI UI が出る。
[ComfyUI 初心者ガイド](ComfyUI_beginner_guide/00_index.md) が画像・音楽生成の最初の一歩をカバーしている。

## 動作確認

```bash
# GPU 認識確認
docker exec comfyui-rocm57 python3 -c "
import torch
print('torch:', torch.__version__)
print('cuda available (HIP):', torch.cuda.is_available())
print('device:', torch.cuda.get_device_name(0))
"

# 期待出力:
# torch: 2.3.1+rocm5.7
# cuda available (HIP): True
# device: AMD Radeon VII

# VRAM 状況
docker exec comfyui-rocm57 rocm-smi --showmeminfo vram
```

## API 経由での生成（curl 例）

```bash
# ワークフロー JSON を投げる
PROMPT_ID=$(curl -s -X POST http://localhost:8188/prompt \
  -d @workflow.json \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['prompt_id'])")

# 完了確認
curl -s http://localhost:8188/history/$PROMPT_ID | python3 -m json.tool

# 画像取得
curl -s "http://localhost:8188/view?filename=ComfyUI_00001_.png&type=output" -o out.png
```

ワークフロー JSON は ComfyUI UI で組んだものを「Save (API Format)」で書き出せる。

## Civitai モデルの取得（付属スクリプト）

`scripts/civitai_download.py` で、Civitai のモデルページ URL から自動で正しいサブディレクトリ（checkpoints / loras / vae / controlnet 等）に振り分けて DL できる。**リポジトリルートから実行**する（compose の `~/comfyui-data/` ではなく、こちら側）。

### 単発 DL

```bash
cd /path/to/Comfyui-docker-for-radeon-vii  # リポジトリルート

# モデルページ URL（最新バージョンが選ばれる）
./scripts/civitai_download.py https://civitai.com/models/133005

# 特定バージョンを固定したい場合
./scripts/civitai_download.py 'https://civitai.com/models/133005?modelVersionId=288982'

# version ID 直接
./scripts/civitai_download.py 288982
```

### 一括 DL（マニフェスト）

```bash
# scripts/models.txt.example をコピーして編集（models.txt は .gitignore 済み）
cp scripts/models.txt.example scripts/models.txt
# URL を1行1件で書く

./scripts/civitai_download.py --manifest scripts/models.txt
```

### API トークン（必要な場合）

NSFW フラグ付きや認証必須モデルは [Civitai のアカウント設定](https://civitai.com/user/account) でトークン発行 → 環境変数にセット:

```bash
export CIVITAI_TOKEN=xxxxxxxxxxxxx
./scripts/civitai_download.py URL
```

`~/.bashrc` に書いておくと便利。

### 仕様

- 既存ファイルがサイズ一致なら **スキップ**（リトライしやすい）
- `Checkpoint` → `models/checkpoints/`、`LORA` → `models/loras/`、`VAE` → `models/vae/`、`Controlnet` → `models/controlnet/` 等に**自動振り分け**
- 進捗表示付き、`.part` ファイルで中断検知可能
- 依存: Python 3.8+ 標準ライブラリのみ（pip install 不要）

## 重要な制約と理由

### ComfyUI を v0.3.60 に pin している理由

ComfyUI v0.3.70 以降は `comfy_kitchen` パッケージ依存になり、`torch.library.custom_op`（PyTorch 2.4+）を要求する。一方 ROCm 5.7 系の PyTorch wheel は最新でも 2.3.1 で止まっている（rocm5.7 ライン終了）。

**選択肢:**
- ComfyUI v0.3.60 で pin（本構成、安定）
- ROCm 6.x + PyTorch 2.4+ で最新 ComfyUI を使う ← gfx906 が deprecated でロード失敗の懸念大

→ **gfx906 を使う限り当面 v0.3.60 が事実上の天井**。新機能を取り込むなら ComfyUI 上流で gfx906 互換を保つフォークが出るのを待つか、PyTorch 2.4 + rocm6.x の組み合わせを実験するしかない。

### ROCm 6.x で gfx906 が deprecated

- 2023 Q3 (ROCm 5.7) で maintenance mode 入り
- 2024 Q2 で security patch も終了
- ROCm 6.4.0 で rocBLAS の TensileLibrary すら同梱されない
- 公式は gfx908+ (MI100, MI200, MI300, RDNA3+) を推奨

このため、**安定版 ROCm で動作保証されている範囲で最も新しい組合せが本構成 (ROCm 5.7 + PyTorch 2.3.1)**。本リポジトリはあえて安定版で構成することを優先しています。

### 補足: ROCm/TheRock での gfx906 サポート動向

[ROCm/TheRock](https://github.com/ROCm/TheRock) は、ROCm/HIP コンポーネント全体を CMake の super-project として **ソースからビルドする OSS ビルドプラットフォーム** です。AMD 公式の package ベース配布の **代替ではなく補完** で、nightly ビルド（ROCm + PyTorch）を提供します。現在 early preview 状態で、対象はコントリビューター・研究者・上級者向け。

TheRock の [SUPPORTED_GPUS.md](https://github.com/ROCm/TheRock/blob/main/SUPPORTED_GPUS.md) は **将来 ROCm 公式リリースに反映される GPU サポートの leading indicator** として機能していて、ここに gfx906 が **「Build Passing」** ステータスで掲載されています（2026年4月現在）。意味:

- ✅ TheRock のビルドが gfx906 向けに通る
- ❌ sanity test は未実施
- ❌ release readiness の指標も未付与

つまり「コードはビルドできるところまで戻ってきたが、動作品質は未保証」の段階です。なお gfx900 (Vega 10) は SUPPORTED_GPUS.md にまだ載っていません。

TheRock を直接使えば nightly な ROCm + PyTorch で gfx906 を試すことは可能ですが、本リポジトリは **「動作実績のある安定版を提供する」** ことを優先し、AMD 公式の最終安定版である **ROCm 5.7 に留まっています**。TheRock 経由のビルドが品質的に十分こなれた段階、あるいは AMD 公式 ROCm 6.x で gfx906 が再採用された段階で、構成の移行を検討する予定です。

#### より新しい ROCm で gfx906 を動かしてみたい場合

[mixa3607/ML-gfx906](https://github.com/mixa3607/ML-gfx906) が TheRock 由来の新しい ROCm（6.3.3 / 7.x 系）で gfx906 (Radeon VII / MI50 / MI60) 向けの Docker イメージを daily 配布しています。ComfyUI に加えて llama.cpp や vLLM のビルドも提供しており、最新版を試したい方や LLM・推論バックエンドも一緒に揃えたい方はそちらが適合します。

本リポジトリと棲み分けのポイント:

| | 本リポジトリ | mixa3607/ML-gfx906 |
|---|---|---|
| ROCm | 5.7（最終公式安定版） | 6.3.3 / 7.x（TheRock 由来） |
| 更新頻度 | pin（安定維持） | daily build |
| scope | ComfyUI 一本 | ComfyUI + llama.cpp + vLLM |
| Docker image | 自前ビルド | Docker Hub 配布あり |

### `HSA_OVERRIDE_GFX_VERSION=9.0.6` が必要

ROCm のランタイムが gfx906 を厳密にチェックする場面で、明示的にこのバージョン文字列を指定しないと `device not supported` エラーになる場合がある。Dockerfile / compose でセット済み。

### `transformers` が一部使えない

`transformers >= 4.x` は `torch >= 2.4` を要求するため、v0.3.60 のコンテナ内では「PyTorch was not found. Models won't be available」と出る。SDXL の基本ワークフローは ComfyUI 内蔵の CLIP/T5 ローダーで完結するため通常は問題ないが、`transformers` 由来の特定ノード（一部の ControlNet 等）は動かない。

## トラブルシューティング

### `permission denied while trying to connect to the docker API`

ユーザーが docker グループに入っていない、または現セッションが古い。
```bash
sudo usermod -aG docker $USER  # まだなら追加
newgrp docker                  # 新シェルで反映
# またはログアウト→ログイン
```

### `Device not found` / GPU 認識せず

- `docker-compose.yml` の `/dev/dri/renderD12X` が Radeon VII になっているか `ls -l /dev/dri/by-path/` で確認（複数 GPU 環境では番号がずれる）
- ホスト側で `/dev/kfd` が存在するか
- コンテナ内で `rocm-smi` が GPU を出力するか

### 生成中にコンテナが OOM-kill / segfault

- VRAM 不足の可能性。`models/checkpoints` の重いモデル（特に Flux 系）は q4/q5 量子化版を使うか、`--lowvram` フラグを `command` に追加
- `--lowvram`/`--medvram` は ComfyUI 起動引数として `docker-compose.yml` の `command` で指定可能

### ビルド失敗 (`pip install torch ... 503/timeout`)

- PyTorch CDN の一時障害。リトライで通ることが多い
- pip cache を効かせるなら `--mount=type=cache,target=/root/.cache/pip` を BuildKit で

### ComfyUI 起動はするが画像生成がエラー

- ComfyUI の起動引数に `--use-split-cross-attention` を追加すると古い AMD で安定する場合あり
- VAE のメモリエラーなら `--bf16-vae` か `--cpu-vae`

### ComfyUI-Manager で `This action is not allowed with this security level configuration.`

カスタムノードのインストール時にこのエラーが出る場合、ComfyUI-Manager が（v0.3.60 pin の本構成で）`security_level` を強制的に `strong` に上書きしているのが原因。`config.ini` の編集に加えて Manager 側にもパッチが必要。詳細と手順は [comfyui-manager-security-level-fix.md](comfyui-manager-security-level-fix.md) を参照。

## 参考リンク

- [ComfyUI 公式](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI 公式サンプルワークフロー](https://comfyanonymous.github.io/ComfyUI_examples/)
- [ROCm gfx906 deprecation 議論](https://github.com/ROCm/ROCm/issues/6138)
- [PyTorch ROCm wheel index](https://download.pytorch.org/whl/rocm5.7/torch/)
- [Civitai (モデル共有)](https://civitai.com/)
- [Hugging Face (モデル共有)](https://huggingface.co/)

## ライセンス

このリポジトリの Dockerfile・compose・README は MIT 相当で自由に利用可。
ComfyUI 本体は GPL v3。
SDXL モデルは [CreativeML Open RAIL++-M](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md)（商用 OK）。
他モデルはそれぞれのライセンスを確認のこと。
