# config.py


import os
from pathlib import Path


def load_env_file(path=".env"):


    env_path = Path(__file__).resolve().parent / path


    if not env_path.exists():


        return


    for line in env_path.read_text(encoding="utf-8").splitlines():


        line = line.strip()


        if not line or line.startswith("#") or "=" not in line:


            continue


        key, value = line.split("=", 1)


        key = key.strip()


        value = value.strip().strip('"').strip("'")


        os.environ.setdefault(

            key,

            value

        )


def env_bool(name, default=False):


    value = os.getenv(name)


    if value is None:


        return default


    return value.strip().lower() in {

        "1",

        "true",

        "yes",

        "on"

    }


def env_int(name, default):


    value = os.getenv(name)


    if value is None:


        return default


    return int(value)


def env_float(name, default):


    value = os.getenv(name)


    if value is None:


        return default


    return float(value)


load_env_file()


# =============================
# LLM
# =============================

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "local"
).lower()


LOCAL_LLM_API = (
    "http://localhost:8000/v1/chat/completions"
)


LOCAL_LLM_MODEL = (
    "mlx-community/Qwen3-4B-4bit"
)


ONLINE_LLM_BASE_URL = os.getenv(
    "ONLINE_LLM_BASE_URL",
    ""
).rstrip("/")


ONLINE_LLM_API = (
    f"{ONLINE_LLM_BASE_URL}/chat/completions"
    if ONLINE_LLM_BASE_URL
    else ""
)


ONLINE_LLM_MODEL = os.getenv(
    "ONLINE_LLM_MODEL",
    "qwen3.5-plus-2026-04-20"
)


ONLINE_LLM_API_KEY = os.getenv(
    "DASHSCOPE_API_KEY",
    ""
)


ONLINE_LLM_STREAM = env_bool(
    "ONLINE_LLM_STREAM",
    True
)


ONLINE_LLM_ENABLE_THINKING = env_bool(
    "ONLINE_LLM_ENABLE_THINKING",
    False
)


LLM_TEMPERATURE = env_float(
    "LLM_TEMPERATURE",
    0.6
)


LLM_MAX_TOKENS = env_int(
    "LLM_MAX_TOKENS",
    100
)


# Backward-compatible aliases for local LLM settings.

LLM_API = LOCAL_LLM_API


LLM_MODEL = LOCAL_LLM_MODEL



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


TTS_VOICE = "Uncle_Fu"


# Qwen3-TTS CustomVoice 可选说话人。
# 参考 QwenLM/Qwen3-TTS 官方说明：
# Vivian / Serena / Uncle_Fu / Dylan / Eric / Ryan / Aiden / Ono_Anna / Sohee

TTS_AVAILABLE_SPEAKERS = {
    "Vivian": "明亮、略带锋芒的年轻女声，中文。",
    "Serena": "温暖、温柔的年轻女声，中文。",
    "Uncle_Fu": "成熟低沉、醇厚的男声，中文。",
    "Dylan": "年轻清晰、自然的北京男声，中文普通话/北京口音。",
    "Eric": "活泼、略带沙哑明亮感的成都男声，中文/四川口音。",
    "Ryan": "节奏感强、富有动感的男声，英文。",
    "Aiden": "阳光清晰的美式男声，英文。",
    "Ono_Anna": "轻快、俏皮的日语女声，日语。",
    "Sohee": "温暖、情感丰富的韩语女声，韩语。",
}


# 语音风格描述。保持固定 instruct 可以让合成语音的情绪、语速、
# 语气更稳定。若不想使用风格控制，可设置为空字符串 ""。

TTS_INSTRUCT = (
    "始终使用同一个稳定的中文男性声音色说话，"
    "语速适中，语调平稳，不要夸张，不要改变情绪，"
    "保持自然、清楚、亲切。"
)


# 语音合成语言。中文建议 zh。

TTS_LANGUAGE = "zh"


# TTS 采样参数。温度越高，声音变化越大；越低越稳定。

TTS_TEMPERATURE = 0.1


TTS_MAX_TOKENS = 1200


# 是否启用 TTS 流式合成 + 播放

TTS_STREAM = True


# 流式 TTS 每次生成的音频块间隔，越小越快开始播放，
# 但过小可能导致声音不够稳定或播放缓冲不足。

TTS_STREAMING_INTERVAL = 0.8


# 播放器启动前预缓冲时长，越小越低延迟，
# 如果出现卡顿或断续，可以调大到 0.8 或 1.0。

TTS_STREAM_MIN_BUFFER_SECONDS = 0.5


# 流式 TTS 防卡死保护。
# 如果 TTS 生成或播放偶发卡住，超过这些时间后会自动结束本轮。

TTS_STREAM_TIMEOUT_SECONDS = 30


TTS_STREAM_DRAIN_TIMEOUT_SECONDS = 15



# =============================
# Audio
# =============================


SAMPLE_RATE = 16000


# 修改成自己的麦克风编号

MIC_DEVICE = 1



# VAD

SILENCE_SECONDS = 0.5

MAX_RECORD_SECONDS = 15
