from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="openai/whisper-large-v3",
    local_dir="/ruta/a/large-v3",
    local_dir_use_symlinks=False
)