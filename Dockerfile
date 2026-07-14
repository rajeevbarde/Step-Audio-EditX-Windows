FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV TZ=Asia/Shanghai
ENV UV_LINK_MODE=copy
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

RUN apt-get update \
    && apt-get install -y build-essential \
    && apt-get install -y wget \
    && apt-get install -y software-properties-common curl zip unzip git-lfs awscli libssl-dev openssh-server vim \
    && apt-get install -y net-tools iputils-ping iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get install --reinstall -y ca-certificates && update-ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python 3.12 (pyproject.toml requires >=3.12,<3.14)
RUN add-apt-repository -y 'ppa:deadsnakes/ppa' && apt update
RUN apt install python3.12 python3.12-dev python3.12-venv -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.12 /usr/bin/python \
    && ln -sf /usr/bin/python3.12 /usr/bin/python3

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync

# torchaudio/torchcodec + sox
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg sox libsox-fmt-all \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# App source (models mounted at runtime to /model)
COPY . .

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
