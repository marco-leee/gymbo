# GPU image for RunPod / any host with NVIDIA Container Toolkit.
# PyTorch + Ultralytics CUDA wheels come from uv.lock; the NVIDIA base image
# aligns the container with the GPU driver.
#
# YOLOv26 checkpoints (`yolo26l.pt`, `yolo26l-pose.pt`, `yolo26l-seg.pt`) live in
# `/app/src/pose_models/`: copied from your repo when present; otherwise fetched at
# build time from Ultralytics GitHub assets (override release with build-arg
# `ULTRALYTICS_ASSETS_RELEASE`). For air-gapped builds, place those files under
# `src/pose_models/` locally before `docker build`.
#
# Build (RunPod / linux amd64):
#   docker build --platform linux/amd64 -t gymbo-yolo-ws .
#
# If apt fails with "invalid signature" / "repository ... is not signed" only when
# using --platform linux/amd64 on Apple Silicon, that is QEMU emulation confusing
# apt gpgv — not a bad CUDA/Ubuntu mirror. Mitigations: Docker Desktop → enable
# "Rosetta for x86_64/amd64 emulation"; update Docker Desktop; or build/push the
# amd64 image on an amd64 host or CI (e.g. ubuntu-latest). As a last resort try:
#   docker build --security-opt seccomp=unconfined --platform linux/amd64 ...
# RunPod load-balanced worker: set PORT=80 (see ai/runpod.py) or expose 10001 for local.
# Local GPU smoke test (defaults to YOLO_WS_PORT=10001 unless PORT is set):
#   docker run --rm --gpus all -p 10001:10001 gymbo-yolo-ws
# RunPod LB (PORT=80 typical):
#   docker run --rm --gpus all -p 80:80 -e PORT=80 gymbo-yolo-ws
# Override weights without rebuild:
#   docker run --rm --gpus all -p 10001:10001 -v "$(pwd)/src/pose_models:/app/src/pose_models:ro" gymbo-yolo-ws

FROM nvidia/cuda:12.1.0-base-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.12 \
        python3.12-venv \
        python3.12-dev \
        libglib2.0-0 \
        libgl1 \
        ffmpeg \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_PYTHON=/usr/bin/python3.12

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src

ARG ULTRALYTICS_ASSETS_RELEASE=v8.4.0
RUN set -eux; \
    mkdir -p /app/src/pose_models; \
    cd /app/src/pose_models; \
    for f in yolo26l.pt yolo26l-pose.pt yolo26l-seg.pt; do \
      if [ ! -s "$f" ]; then \
        curl -fsSL -o "$f" \
          "https://github.com/ultralytics/assets/releases/download/${ULTRALYTICS_ASSETS_RELEASE}/$f"; \
      fi; \
    done

ENV PYTHONPATH=/app/src
RUN uv sync --frozen --no-dev

# Default image port for local/smoke tests; RunPod LB often maps container PORT=80.

EXPOSE 80

CMD ["uv", "run", "--directory", "/app", "--no-dev", "python", "src/yolo_fastapi_main.py"]
