"""
Download required models

Run:

python download.py

"""


from huggingface_hub import snapshot_download



MODELS = [


"mlx-community/Qwen3-4B-4bit",


"mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-4bit",


"mlx-community/Qwen3-ASR-1.7B-8bit"


]



for model in MODELS:


    print(
        "\nDownloading:",
        model
    )


    snapshot_download(

        repo_id=model

    )


    print(
        "Done:",
        model
    )



print(
    "\nAll models downloaded."
)
