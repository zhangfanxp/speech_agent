# Speech Agent

A local-first Chinese voice assistant optimized for Apple Silicon Mac.

基于 Apple Silicon + MLX 的中文语音助手，支持本地 ASR、本地 TTS、本地或线上 LLM。

## Features

- 🎤 Microphone voice input on macOS
- ⚡ Silero VAD automatic speech detection
- 📝 Qwen3-ASR speech recognition
- 🧠 Local or online OpenAI-compatible LLM
- 🔊 Qwen3-TTS Chinese speech synthesis
- 🌊 Streaming TTS playback for lower perceived latency
- 🧩 Configurable system prompt via `prompt.json`
- 🗣️ Configurable TTS speaker, style instruction, and sampling parameters
- 🔒 Local-first workflow; secrets are stored in `.env`

## Architecture

```text
Microphone
  ↓
Silero VAD
  ↓
Qwen3-ASR
  ↓
LLM
  ├─ local: mlx-community/Qwen3-4B-4bit
  └─ online: OpenAI-compatible API
  ↓
Qwen3-TTS streaming synthesis
  ↓
Speaker / Headphones
```

## Requirements

Recommended hardware:

- Apple Silicon Mac
- 16GB RAM or above
- macOS

Tested on:

- Mac mini M4
- 16GB RAM

## Models

This project uses:

| Component | Model |
|---|---|
| Local LLM | `mlx-community/Qwen3-4B-4bit` |
| ASR | `mlx-community/Qwen3-ASR-1.7B-8bit` |
| TTS | `mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-4bit` |

Models are downloaded from Hugging Face.

## Installation

Install audio dependency:

```bash
brew install ffmpeg
```

Install `uv`:

```bash
brew install uv
```

Create and activate Python environment:

```bash
uv venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
uv pip install -r requirements.txt
```

Download models:

```bash
python download.py
```

## Environment config

Copy the example env file:

```bash
cp .env.example .env
```

Edit `.env` to choose the LLM provider.

Use online LLM:

```env
LLM_PROVIDER=online
DASHSCOPE_API_KEY=请填写你的阿里百炼API_KEY
ONLINE_LLM_BASE_URL=请填写你的OpenAI兼容接口地址
ONLINE_LLM_MODEL=请填写线上LLM模型名称
ONLINE_LLM_STREAM=true
ONLINE_LLM_ENABLE_THINKING=false
```

Use local LLM:

```env
LLM_PROVIDER=local
```

`.env` is ignored by Git. Do not upload real API keys to GitHub.

## Prompt config

The LLM system prompt is stored in:

```text
prompt.json
```

Edit `system_prompt` to change the assistant behavior without modifying `app.py`.

Example:

```json
{
  "system_prompt": "你是一个中文语音助手。回答要简短、自然，适合直接朗读。"
}
```

## TTS config

TTS settings are in `config.py`.

Current speaker:

```python
TTS_VOICE = "Vivian"
```

Available Qwen3-TTS CustomVoice speakers:

- `Vivian`
- `Serena`
- `Uncle_Fu`
- `Dylan`
- `Eric`
- `Ryan`
- `Aiden`
- `Ono_Anna`
- `Sohee`

Voice style instruction:

```python
TTS_INSTRUCT = (
    "始终使用同一个稳定的中文女声音色说话，"
    "语速适中，语调平稳，不要夸张，不要改变情绪，"
    "保持自然、清楚、亲切。"
)
```

For more stable voice output, lower temperature is recommended:

```python
TTS_TEMPERATURE = 0.3
```

Streaming TTS is enabled by default:

```python
TTS_STREAM = True
TTS_STREAMING_INTERVAL = 0.8
TTS_STREAM_MIN_BUFFER_SECONDS = 0.5
TTS_STREAM_TIMEOUT_SECONDS = 30
TTS_STREAM_DRAIN_TIMEOUT_SECONDS = 15
```

If playback is choppy, increase `TTS_STREAM_MIN_BUFFER_SECONDS` to `0.8` or `1.0`.

If streaming TTS occasionally hangs, the timeout settings above will stop the current playback round and return the assistant to listening mode.

## Configure microphone

List audio devices:

```bash
python -c "import sounddevice as sd;print(sd.query_devices())"
```

Edit `config.py`:

```python
MIC_DEVICE = 1
```

Set it to your microphone device index.

## Running

If using online LLM:

```bash
./run.sh
```

If using local LLM, start the local LLM server in terminal 1:

```bash
./start_llm.sh
```

Then start the voice assistant in terminal 2:

```bash
./run.sh
```

You should see logs similar to:

```text
已加载提示词配置: prompt.json
加载 Silero VAD...
加载 Qwen3-ASR...
加载 Qwen3-TTS...
TTS模式: 流式播放
模型加载完成
LLM模式: 线上 (...)
🎤 等待讲话...
```

## Voice commands

Say one of the following to exit:

- 退出
- 再见
- 退下
- 结束
- 关闭
- 停止
- 拜拜

## Latency notes

The most important conversational latency is:

```text
用户说完到开始播放
```

With streaming TTS enabled, this project logs:

```text
⏱ ASR识别耗时
⏱ LLM生成耗时
⏱ TTS首个音频块耗时
⏱ 流式播放启动耗时
⏱ 用户说完到开始播放
```

Typical optimized latency on Apple Silicon is around 1–1.5 seconds from user speech end to first AI audio, depending on ASR, LLM provider, and answer length.

## Project structure

```text
speech_agent
├── app.py
├── config.py
├── prompt.json
├── .env.example
├── download.py
├── requirements.txt
├── run.sh
├── start_llm.sh
├── README.md
├── LICENSE
└── scripts
```

## Troubleshooting

No microphone detected:

```bash
python -c "import sounddevice as sd;print(sd.query_devices())"
```

Local LLM server unavailable:

```bash
curl http://localhost:8000/v1/models
```

TTS voice changes too much between runs:

- Lower `TTS_TEMPERATURE`
- Keep `TTS_VOICE` fixed
- Use a stable `TTS_INSTRUCT`

Streaming playback is choppy:

- Increase `TTS_STREAM_MIN_BUFFER_SECONDS`
- Try `TTS_STREAMING_INTERVAL = 0.8` or higher

Streaming TTS hangs:

- Keep `TTS_STREAM_TIMEOUT_SECONDS` enabled
- Increase `TTS_STREAMING_INTERVAL`
- Try a slightly higher `TTS_TEMPERATURE` such as `0.3` if the voice sounds too constrained

## Credits

Inspired by:

- [Hugging Face Speech-to-Speech](https://github.com/huggingface/speech-to-speech)
- [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)

Optimized for Apple Silicon using:

- MLX
- mlx-lm
- mlx-audio

## License

MIT License
