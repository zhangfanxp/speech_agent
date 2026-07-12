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


# 是否启用 TTS 流式合成 + 播放

TTS_STREAM = True


# 流式 TTS 每次生成的音频块间隔，越小越快开始播放，
# 但过小可能导致声音不够稳定或播放缓冲不足。

TTS_STREAMING_INTERVAL = 0.5


# 播放器启动前预缓冲时长，越小越低延迟，
# 如果出现卡顿或断续，可以调大到 0.8 或 1.0。

TTS_STREAM_MIN_BUFFER_SECONDS = 0.5



# =============================
# Audio
# =============================


SAMPLE_RATE = 16000


# 修改成自己的麦克风编号

MIC_DEVICE = 1



# VAD

SILENCE_SECONDS = 0.5

MAX_RECORD_SECONDS = 15
