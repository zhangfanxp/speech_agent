import time
import requests
import subprocess
import glob
import os
import json
from pathlib import Path

import numpy as np
import torch

import sounddevice as sd
import soundfile as sf


from silero_vad import load_silero_vad


from mlx_audio.stt.utils import load_model as load_asr_model

from mlx_audio.tts.utils import load_model as load_tts_model

from mlx_audio.tts.generate import generate_audio

from mlx_audio.tts.audio_player import AudioPlayer



from config import (

    LLM_PROVIDER,

    LOCAL_LLM_API,

    LOCAL_LLM_MODEL,

    ONLINE_LLM_API,

    ONLINE_LLM_MODEL,

    ONLINE_LLM_API_KEY,

    ONLINE_LLM_STREAM,

    ONLINE_LLM_ENABLE_THINKING,

    LLM_TEMPERATURE,

    LLM_MAX_TOKENS,


    ASR_MODEL,


    TTS_MODEL,

    TTS_VOICE,

    TTS_AVAILABLE_SPEAKERS,

    TTS_INSTRUCT,

    TTS_LANGUAGE,

    TTS_TEMPERATURE,

    TTS_TOP_K,

    TTS_TOP_P,

    TTS_REPETITION_PENALTY,

    TTS_MAX_TOKENS,

    TTS_MAX_AUDIO_SECONDS,

    TTS_STREAM,

    TTS_STREAMING_INTERVAL,

    TTS_STREAM_MIN_BUFFER_SECONDS,

    TTS_STREAM_TIMEOUT_SECONDS,

    TTS_STREAM_DRAIN_TIMEOUT_SECONDS,

    TTS_STREAM_DRAIN_TIMEOUT_EXTRA_SECONDS,


    SAMPLE_RATE,

    MIC_DEVICE,


    SILENCE_SECONDS,

    MAX_RECORD_SECONDS

)





# =====================================
# System Prompt
# =====================================


DEFAULT_SYSTEM_PROMPT = """

你是一个本地中文语音助手。

回答要求：

1. 使用中文回答。
2. 使用简洁自然的口语。
3. 不输出思考过程。
4. 不解释推理步骤。
5. 不使用列表。
6. 回复适合语音播放。
7. 普通回答控制在50字以内。

"""


def load_system_prompt(path="prompt.json"):


    prompt_path = Path(__file__).resolve().parent / path


    try:


        data = json.loads(

            prompt_path.read_text(

                encoding="utf-8"

            )

        )


        prompt = data.get(

            "system_prompt",

            ""

        ).strip()


        if prompt:


            print(

                f"已加载提示词配置: {prompt_path.name}"

            )


            return prompt


        print(

            f"提示词配置为空，使用默认提示词: {prompt_path.name}"

        )


    except FileNotFoundError:


        print(

            f"未找到提示词配置，使用默认提示词: {prompt_path.name}"

        )


    except Exception as e:


        print(

            "提示词配置读取失败，使用默认提示词:",

            e

        )


    return DEFAULT_SYSTEM_PROMPT.strip()


SYSTEM_PROMPT = load_system_prompt()





# =====================================
# 退出关键词
# =====================================


EXIT_COMMANDS = [

    "退出",

    "再见",

    "退下",

    "结束",

    "关闭",

    "停止",

    "拜拜"

]



# =====================================
# 耗时日志
# =====================================


def now():


    return time.perf_counter()



def format_seconds(seconds):


    return f"{seconds:.2f}s"



def log_duration(label, seconds):


    print(

        f"⏱ {label}: {format_seconds(seconds)}"

    )



def print_turn_timing(timing):


    total = timing["play_end"] - timing["turn_start"]


    response_latency = timing["play_start"] - timing["record_end"]


    is_streaming = timing.get(

        "tts_streaming",

        False

    )


    print(

        "\n⏱ 本轮耗时统计"

    )


    print(

        "- 录音阶段:",

        format_seconds(timing["record_end"] - timing["turn_start"])

    )


    print(

        "- ASR识别:",

        format_seconds(timing["asr_end"] - timing["record_end"])

    )


    print(

        "- LLM生成:",

        format_seconds(timing["llm_end"] - timing["asr_end"])

    )


    if is_streaming:


        print(

            "- TTS首个音频块:",

            format_seconds(timing["first_audio_chunk"] - timing["llm_end"])

        )


        print(

            "- 流式播放启动:",

            format_seconds(timing["play_start"] - timing["llm_end"])

        )


        print(

            "- 流式TTS+播放:",

            format_seconds(timing["play_end"] - timing["llm_end"])

        )


    else:


        print(

            "- TTS合成:",

            format_seconds(timing["tts_end"] - timing["llm_end"])

        )


        print(

            "- 音频播放:",

            format_seconds(timing["play_end"] - timing["play_start"])

        )


    print(

        "- 用户说完到开始播放:",

        format_seconds(response_latency)

    )


    print(

        "- 本轮总耗时:",

        format_seconds(total)

    )





# =====================================
# 加载模型
# =====================================


print("加载 Silero VAD...")


vad_model = load_silero_vad()



print("加载 Qwen3-ASR...")


asr_model = load_asr_model(

    ASR_MODEL

)



print(

    "加载 Qwen3-TTS...",

    flush=True

)


tts_load_start = now()


tts_model = load_tts_model(

    TTS_MODEL,

    lazy=True

)


log_duration(

    "Qwen3-TTS加载耗时",

    now() - tts_load_start

)


if TTS_STREAM:


    print(

        f"TTS模式: 流式播放 "

        f"(interval={TTS_STREAMING_INTERVAL}s, "

        f"buffer={TTS_STREAM_MIN_BUFFER_SECONDS}s, "

        f"timeout={TTS_STREAM_TIMEOUT_SECONDS}s)"

    )


else:


    print(

        "TTS模式: 生成完整wav后播放"

    )


print(

    f"TTS说话人: {TTS_VOICE}"

)


speaker_description = TTS_AVAILABLE_SPEAKERS.get(

    TTS_VOICE,

    "未在配置清单中找到该说话人描述"

)


print(

    f"TTS说话人描述: {speaker_description}"

)


if TTS_INSTRUCT:


    print(

        f"TTS风格描述: {TTS_INSTRUCT}"

    )



print("\n模型加载完成\n")


if LLM_PROVIDER == "online":


    print(

        f"LLM模式: 线上 ({ONLINE_LLM_MODEL})"

    )


else:


    print(

        f"LLM模式: 本地 ({LOCAL_LLM_MODEL})"

    )







# =====================================
# Silero VAD录音
# =====================================


def record_audio_vad():


    print(

        "🎤 等待讲话..."

    )



    audio_chunks = []


    started = False


    silence_start = None



    chunk_size = 512



    record_start = now()


    speech_start = None


    start_time = time.time()



    with sd.InputStream(


        samplerate=SAMPLE_RATE,


        channels=1,


        dtype="float32",


        blocksize=chunk_size,


        device=MIC_DEVICE


    ) as stream:



        while True:



            audio, overflow = stream.read(

                chunk_size

            )



            audio = audio.reshape(-1)



            audio_chunks.append(audio)



            tensor_audio = torch.tensor(

                audio

            )



            if len(tensor_audio) >= 512:



                speech_prob = vad_model(

                    tensor_audio,

                    SAMPLE_RATE

                ).item()



                if speech_prob > 0.5:



                    if not started:

                        print(

                            "检测到讲话"

                        )

                        speech_start = now()


                    started = True

                    silence_start = None



                elif started:



                    if silence_start is None:


                        silence_start = time.time()



                    elif (

                        time.time()

                        -

                        silence_start

                        >

                        SILENCE_SECONDS

                    ):


                        break




            if (

                time.time()

                -

                start_time

                >

                MAX_RECORD_SECONDS

            ):


                break





    audio_data = np.concatenate(

        audio_chunks

    )



    sf.write(

        "input.wav",

        audio_data,

        SAMPLE_RATE

    )


    print(

        "录音完成"

    )


    audio_duration = len(audio_data) / SAMPLE_RATE


    record_elapsed = now() - record_start


    if speech_start is None:


        wait_elapsed = record_elapsed


    else:


        wait_elapsed = speech_start - record_start


    log_duration(

        "等待开口",

        wait_elapsed

    )


    log_duration(

        "录音阶段总耗时",

        record_elapsed

    )


    print(

        f"⏱ 录音音频长度: {format_seconds(audio_duration)}"

    )

# =====================================
# ASR 语音识别
# =====================================


def speech_to_text():


    print(

        "📝 正在识别..."

    )


    asr_start = now()



    result = asr_model.generate(

        "input.wav",

        language="Chinese",

        verbose=False

    )



    text = result.text.strip()



    print(

        "用户:",

        text

    )


    log_duration(

        "ASR识别耗时",

        now() - asr_start

    )



    return text






# =====================================
# 判断退出
# =====================================


def should_exit(text):


    for cmd in EXIT_COMMANDS:


        if cmd in text:


            return True



    return False






# =====================================
# LLM
# =====================================


def build_chat_messages(text):


    return [

        {

            "role": "system",

            "content": SYSTEM_PROMPT

        },

        {

            "role": "user",

            "content": text

        }

    ]



def chat_local(text):


    payload = {

        "model": LOCAL_LLM_MODEL,

        "messages": build_chat_messages(

            text

        ),

        "temperature": LLM_TEMPERATURE,

        "max_tokens": LLM_MAX_TOKENS,

        # Qwen3关闭thinking

        "chat_template_kwargs": {

            "enable_thinking": False

        }

    }


    response = requests.post(

        LOCAL_LLM_API,

        json=payload,

        timeout=120

    )


    response.raise_for_status()


    result = response.json()


    return (

        result

        ["choices"]

        [0]

        ["message"]

        ["content"]

        .strip()

    )



def collect_online_stream(response):


    parts = []


    for line in response.iter_lines(

        decode_unicode=True

    ):


        if not line:


            continue


        if line.startswith("data:"):


            line = line[len("data:"):].strip()


        if line == "[DONE]":


            break


        try:


            event = json.loads(

                line

            )


        except json.JSONDecodeError:


            continue


        choices = event.get(

            "choices",

            []

        )


        if not choices:


            continue


        delta = choices[0].get(

            "delta",

            {}

        )


        content = delta.get(

            "content"

        )


        if content:


            parts.append(

                content

            )


    return "".join(

        parts

    ).strip()



def chat_online(text):


    if not ONLINE_LLM_API:


        raise RuntimeError(

            "ONLINE_LLM_BASE_URL 未配置"

        )


    if not ONLINE_LLM_API_KEY:


        raise RuntimeError(

            "DASHSCOPE_API_KEY 未配置"

        )


    payload = {

        "model": ONLINE_LLM_MODEL,

        "messages": build_chat_messages(

            text

        ),

        "temperature": LLM_TEMPERATURE,

        "max_tokens": LLM_MAX_TOKENS,

        "stream": ONLINE_LLM_STREAM,

        "enable_thinking": ONLINE_LLM_ENABLE_THINKING

    }


    headers = {

        "Authorization": f"Bearer {ONLINE_LLM_API_KEY}",

        "Content-Type": "application/json"

    }


    response = requests.post(

        ONLINE_LLM_API,

        headers=headers,

        json=payload,

        stream=ONLINE_LLM_STREAM,

        timeout=120

    )


    response.raise_for_status()


    if ONLINE_LLM_STREAM:


        return collect_online_stream(

            response

        )


    result = response.json()


    return (

        result

        ["choices"]

        [0]

        ["message"]

        ["content"]

        .strip()

    )



def chat(text):


    print(

        "🧠 AI生成回答..."

    )


    llm_start = now()


    if LLM_PROVIDER == "online":


        answer = chat_online(

            text

        )


    else:


        answer = chat_local(

            text

        )


    print(

        "AI:",

        answer

    )


    log_duration(

        "LLM生成耗时",

        now() - llm_start

    )


    return answer






# =====================================
# TTS语音合成
# =====================================


def text_to_speech(text):


    print(

        "🔊 生成语音..."

    )


    tts_start = now()



    # 清理旧文件

    for f in glob.glob(

        "output*.wav"

    ):

        try:

            os.remove(f)

        except:

            pass





    generate_audio(


        model=tts_model,


        text=text,


        voice=TTS_VOICE,


        instruct=TTS_INSTRUCT,


        lang_code=TTS_LANGUAGE,


        temperature=TTS_TEMPERATURE,


        top_k=TTS_TOP_K,


        top_p=TTS_TOP_P,


        repetition_penalty=TTS_REPETITION_PENALTY,


        max_tokens=TTS_MAX_TOKENS,


        file_prefix="output"


    )



    files = glob.glob(

        "output*.wav"

    )



    if not files:


        raise Exception(

            "TTS没有生成音频"

        )



    output_file = max(


        files,


        key=os.path.getmtime


    )



    print(

        "生成文件:",

        output_file

    )


    log_duration(

        "TTS合成总耗时",

        now() - tts_start

    )



    return output_file





def stream_text_to_speech(text):


    print(

        "🔊 流式生成并播放语音..."

    )


    print(

        "Text:",

        text

    )


    print(

        "Voice:",

        TTS_VOICE

    )


    if TTS_INSTRUCT:


        print(

            "Instruct:",

            TTS_INSTRUCT

        )


    print(

        "Streaming interval:",

        f"{TTS_STREAMING_INTERVAL}s"

    )


    print(

        "Stream timeout:",

        f"{TTS_STREAM_TIMEOUT_SECONDS}s"

    )


    print(

        "Sampling:",

        f"temperature={TTS_TEMPERATURE}, "

        f"top_p={TTS_TOP_P}, "

        f"top_k={TTS_TOP_K}, "

        f"repetition_penalty={TTS_REPETITION_PENALTY}, "

        f"max_audio={TTS_MAX_AUDIO_SECONDS}s"

    )


    stream_start = now()


    first_audio_chunk = None


    play_start = None


    chunk_count = 0


    total_samples = 0


    player = AudioPlayer(

        sample_rate=tts_model.sample_rate

    )


    player.min_buffer_seconds = TTS_STREAM_MIN_BUFFER_SECONDS

    drained = True


    try:


        results = tts_model.generate(

            text=text,

            voice=TTS_VOICE,

            instruct=TTS_INSTRUCT,

            lang_code=TTS_LANGUAGE,

            max_tokens=TTS_MAX_TOKENS,

            temperature=TTS_TEMPERATURE,

            top_k=TTS_TOP_K,

            top_p=TTS_TOP_P,

            repetition_penalty=TTS_REPETITION_PENALTY,

            stream=True,

            streaming_interval=TTS_STREAMING_INTERVAL,

            verbose=False

        )


        for result in results:


            elapsed = now() - stream_start


            if elapsed > TTS_STREAM_TIMEOUT_SECONDS:


                print(

                    "⚠️ 流式TTS生成超时，结束本轮播放"

                )


                break


            chunk_count += 1


            total_samples += result.samples


            generated_audio_seconds = (

                total_samples

                /

                tts_model.sample_rate

            )


            if generated_audio_seconds > TTS_MAX_AUDIO_SECONDS:


                print(

                    "⚠️ 流式TTS音频过长，可能出现重复生成，结束本轮播放"

                )


                break


            if first_audio_chunk is None:


                first_audio_chunk = now()


                log_duration(

                    "TTS首个音频块耗时",

                    first_audio_chunk - stream_start

                )


            player.queue_audio(

                result.audio

            )


            if play_start is None and player.playing:


                play_start = now()


                log_duration(

                    "流式播放启动耗时",

                    play_start - stream_start

                )


        buffered_samples = player.buffered_samples()


        if play_start is None and buffered_samples > 0:


            play_start = now()


        # AudioPlayer 的 drain_event 可能曾因中途缓冲耗尽而被置位。
        # 如果最终缓冲区里仍有音频，需要重新启动/清理 drain 状态，
        # 否则可能出现“还有十几秒缓冲音频，但本轮立刻结束”的情况。
        if buffered_samples > 0:


            if not player.playing:


                player.start_stream()


            else:


                player.drain_event.clear()


        buffered_seconds = (

            buffered_samples

            /

            tts_model.sample_rate

        )


        drain_timeout = max(

            TTS_STREAM_DRAIN_TIMEOUT_SECONDS,

            buffered_seconds + TTS_STREAM_DRAIN_TIMEOUT_EXTRA_SECONDS

        )


        print(

            f"流式播放剩余缓冲: {format_seconds(buffered_seconds)}，"

            f"等待播放完成超时: {format_seconds(drain_timeout)}"

        )


        if buffered_samples > 0 or player.playing:


            drained = player.drain_event.wait(

                timeout=drain_timeout

            )


            if not drained:


                print(

                    "⚠️ 流式音频播放等待超时，强制结束本轮播放"

                )


    finally:


        if drained:


            player.stop()


        else:


            player.flush()


    stream_end = now()


    if first_audio_chunk is None:


        first_audio_chunk = stream_end


    if play_start is None:


        play_start = stream_end


    audio_duration = total_samples / tts_model.sample_rate


    print(

        f"流式音频块数量: {chunk_count}"

    )


    print(

        f"流式音频总长度: {format_seconds(audio_duration)}"

    )


    log_duration(

        "流式TTS+播放总耗时",

        stream_end - stream_start

    )


    return {

        "tts_streaming": True,

        "first_audio_chunk": first_audio_chunk,

        "tts_end": stream_end,

        "play_start": play_start,

        "play_end": stream_end

    }




def speak_text(text):


    if TTS_STREAM:


        return stream_text_to_speech(

            text

        )


    audio = text_to_speech(

        text

    )


    tts_end = now()


    play_start = now()


    play_audio(

        audio

    )


    play_end = now()


    return {

        "tts_streaming": False,

        "tts_end": tts_end,

        "play_start": play_start,

        "play_end": play_end

    }






# =====================================
# 播放音频
# =====================================


def play_audio(file):


    print(

        "▶ 播放:",

        file

    )


    play_start = now()



    subprocess.run(

        [

            "afplay",

            file

        ]

    )


    log_duration(

        "音频播放耗时",

        now() - play_start

    )






# =====================================
# 主程序
# =====================================


def main():


    while True:


        try:



            timing = {

                "turn_start": now()

            }



            # 等待讲话

            record_audio_vad()



            timing["record_end"] = now()



            # ASR

            text = speech_to_text()



            timing["asr_end"] = now()



            if not text:


                continue





            # ==========================
            # 退出逻辑
            # ==========================


            if should_exit(text):


                goodbye = (

                    "好的，再见，"

                    "期待下次和你聊天。"

                )



                print(

                    "AI:",

                    goodbye

                )



                timing["llm_end"] = timing["asr_end"]



                speech_timing = speak_text(

                    goodbye

                )


                timing.update(

                    speech_timing

                )


                print_turn_timing(

                    timing

                )



                print(

                    "\n退出 Voice Agent"

                )



                break





            # ==========================
            # 正常对话
            # ==========================


            answer = chat(text)



            timing["llm_end"] = now()



            if answer:


                speech_timing = speak_text(

                    answer

                )


                timing.update(

                    speech_timing

                )


                print_turn_timing(

                    timing

                )



            print(

                "\n====================\n"

            )




        except KeyboardInterrupt:


            print(

                "\n退出 Voice Agent"

            )


            break




        except Exception as e:


            print(

                "错误:",

                e

            )


            time.sleep(1)







if __name__ == "__main__":


    main()
