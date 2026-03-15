FROM python:3.10-slim

# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures logs are flushed immediately
ENV PYTHONUNBUFFERED 1

# Install system dependencies for OpenCV, MediaPipe, and git (needed for SAM2 install)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- PyTorch (CPU-only) ---
# Must be installed before SAM2, using the official PyTorch CPU wheel index.
RUN pip install --no-cache-dir \
    torch==2.3.1+cpu \
    torchvision==0.18.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# --- SAM2 ---
# Install from source; no official PyPI release yet.
RUN pip install --no-cache-dir \
    "git+https://github.com/facebookresearch/segment-anything-2.git"

# Pre-download SAM2 tiny checkpoint (~40MB) so the worker never fetches at runtime.
# Stored at /app/sam2_hiera_tiny.pt — matches the constant in worker.py.
RUN python3 -c "\
    import urllib.request; \
    urllib.request.urlretrieve(\
    'https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt', \
    '/app/sam2_hiera_tiny.pt'\
    )"

# --- Other dependencies ---
COPY requirements.txt .
COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements.txt -r requirements-test.txt

# Copy application code
COPY . .
