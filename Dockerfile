# ComfyUI on ROCm 5.7 for Radeon VII (gfx906)
# Base: AMD official ROCm 5.7 dev image (last with full gfx906 support)
FROM rocm/dev-ubuntu-22.04:5.7-complete

ENV DEBIAN_FRONTEND=noninteractive

# System deps (most already in rocm dev image)
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip \
        git \
        wget \
        ca-certificates \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# PyTorch with ROCm 5.7 (gfx906-compatible).
# 2.3.1 is the latest in the rocm5.7 wheel line; gfx906 still works at this version.
# torchaudio 2.3.1 is on the same channel and unlocks ComfyUI's audio nodes.
RUN pip3 install --no-cache-dir \
        torch==2.3.1+rocm5.7 \
        torchvision==0.18.1+rocm5.7 \
        torchaudio==2.3.1+rocm5.7 \
        --index-url https://download.pytorch.org/whl/rocm5.7

# ComfyUI is pinned to v0.3.60 — last release before comfy_kitchen / quant_ops.py
# was integrated. v0.3.70+ requires torch>=2.4 via torch.library.custom_op which
# the rocm5.7 wheel line does not have.
WORKDIR /workspace
RUN git clone --branch v0.3.60 --depth 1 https://github.com/comfyanonymous/ComfyUI.git

WORKDIR /workspace/ComfyUI
RUN pip3 install --no-cache-dir -r requirements.txt

# v0.3.60 の requirements.txt には requests が含まれていないので明示的に追加
RUN pip3 install --no-cache-dir requests

# HSA override needed for ROCm runtime to recognize gfx906 in newer toolkits
ENV HSA_OVERRIDE_GFX_VERSION=9.0.6
ENV PYTORCH_ROCM_ARCH=gfx906

EXPOSE 8188
CMD ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
