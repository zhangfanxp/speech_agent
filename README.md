# Speech Agent

A local AI voice assistant optimized for Apple Silicon Mac.

基于 Apple Silicon + MLX 的本地中文语音助手。


## Features

- 🎤 Real-time voice conversation
- 🧠 Local LLM inference
- 🔊 Chinese speech synthesis
- 📝 Qwen3-ASR speech recognition
- ⚡ Silero VAD automatic voice detection
- 🔒 Fully local deployment
- 🚀 Optimized for Apple Silicon


Architecture:


Microphone

↓

Silero VAD

↓

Qwen3-ASR

↓

Qwen3-4B LLM

↓

Qwen3-TTS

↓

Speaker



---

# Requirements


## Hardware

Recommended:

- Apple Silicon Mac
- M4 Mac mini
- M4 MacBook Air
- M4 MacBook Pro
- Memory: 16GB or above


Test environment:


Mac mini M4
16GB RAM
macOS 26



---

# Models


This project uses:


## LLM


mlx-community/Qwen3-4B-4bit



## Speech Recognition


mlx-community/Qwen3-ASR-1.7B-8bit



## Text To Speech


mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-4bit



Models are downloaded automatically from HuggingFace.



---

# Installation


## 1. Install Homebrew


If you don't have Homebrew:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Install audio dependencies:

brew install ffmpeg
2. Install uv

Install Python package manager:

brew install uv

Check:

uv --version
3. Clone project
git clone https://github.com/yourname/speech_agent.git

cd speech_agent
4. Create Python environment

Create virtual environment:

uv venv

Activate:

source .venv/bin/activate
5. Install dependencies
uv pip install -r requirements.txt

Installation may take several minutes.

Download Models

Run:

python download.py

The following models will be downloaded:

Qwen3-4B-4bit

Qwen3-TTS-12Hz-0.6B-CustomVoice-4bit

Qwen3-ASR-1.7B-8bit

Model size:

approximately 9GB-12GB.

Configure Microphone

Check audio devices:

python -c "import sounddevice as sd;print(sd.query_devices())"

Example:

0 Mac mini Microphone
1 QCY-T8
2 Mac mini Speaker

Edit:

config.py

Modify:

MIC_DEVICE = 1

according to your microphone.

Running

This project requires two terminals.

Terminal 1

Start Qwen3 LLM server:

mlx_lm.server \
--model mlx-community/Qwen3-4B-4bit \
--host 0.0.0.0 \
--port 8000

Wait until:

Starting httpd at 0.0.0.0 on port 8000
Terminal 2

Activate environment:

source .venv/bin/activate

Start voice assistant:

python app.py

You should see:

模型加载完成

🎤 等待讲话...

Now you can speak.

Voice Commands

Exit:

退出

再见

结束

关闭

停止

Example:

用户:
退出


AI:
好的，再见，期待下次和你聊天。
Performance

Test:

Mac mini M4
16GB RAM

Typical latency:

Short answer:

3 seconds

Long answer:

5-8 seconds

Memory usage:

5GB-8GB
Project Structure
speech_agent

├── app.py

├── config.py

├── download.py

├── requirements.txt

├── README.md

├── LICENSE

├── .gitignore

└── audio

Troubleshooting
1. No microphone detected

Run:

python -c "import sounddevice as sd;print(sd.query_devices())"

Modify:

config.py

MIC_DEVICE

2. Qwen3 server unavailable

Check:

curl http://localhost:8000/v1/models

Expected:

{
"object":"list"
}
3. TTS generation failed

Delete old audio:

rm output*.wav

Restart:

python app.py
Credits

Inspired by:

HuggingFace Speech-to-Speech:

https://github.com/huggingface/speech-to-speech

Optimized for Apple Silicon using:

MLX
mlx-lm
mlx-audio
License

MIT License


---

## 我建议你再补两个小文件

你的 GitHub 项目会更完整：

### 1. `start_llm.sh`

```bash
#!/bin/bash

mlx_lm.server \
--model mlx-community/Qwen3-4B-4bit \
--host 0.0.0.0 \
--port 8000
2. run_agent.sh
#!/bin/bash

source .venv/bin/activate

python app.py

然后：

chmod +x *.sh

以后别人运行：

终端1：

./start_llm.sh

终端2：

./run_agent.sh
