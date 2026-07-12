# config.py


# =============================
# LLM
# =============================

LLM_API = (
    "http://localhost:8000/v1/chat/completions"
)


LLM_MODEL = (
    "mlx-community/Qwen3-4B-4bit"
)



# =============================
# ASR
# =============================

ASR_MODEL = (
    "mlx-community/"
    "Qwen3-ASR-1.7B-8bit"
)



# =============================
# TTS
# =============================

TTS_MODEL = (
    "mlx-community/"
    "Qwen3-TTS-12Hz-0.6B-CustomVoice-4bit"
)


TTS_VOICE = "Vivian"



# =============================
# Audio
# =============================


SAMPLE_RATE = 16000


# 修改成自己的麦克风编号

MIC_DEVICE = 1



# VAD

SILENCE_SECONDS = 0.8

MAX_RECORD_SECONDS = 15
