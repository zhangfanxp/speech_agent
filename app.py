import time
import requests
import subprocess
import glob
import os

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

    LLM_API,

    LLM_MODEL,


    ASR_MODEL,


    TTS_MODEL,

    TTS_VOICE,

    TTS_STREAM,

    TTS_STREAMING_INTERVAL,

    TTS_STREAM_MIN_BUFFER_SECONDS,


    SAMPLE_RATE,

    MIC_DEVICE,


    SILENCE_SECONDS,

    MAX_RECORD_SECONDS

)





# =====================================
# System Prompt
# =====================================


SYSTEM_PROMPT = """

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



print("加载 Qwen3-TTS...")


tts_model = load_tts_model(

    TTS_MODEL

)


if TTS_STREAM:


    print(

        f"TTS模式: 流式播放 "

        f"(interval={TTS_STREAMING_INTERVAL}s, "

        f"buffer={TTS_STREAM_MIN_BUFFER_SECONDS}s)"

    )


else:


    print(

        "TTS模式: 生成完整wav后播放"

    )



print("\n模型加载完成\n")







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
# Qwen3 LLM
# =====================================


def chat(text):


    print(

        "🧠 AI生成回答..."

    )


    llm_start = now()



    payload = {


        "model":

            LLM_MODEL,



        "messages":

        [

            {


                "role":

                    "system",


                "content":

                    SYSTEM_PROMPT


            },


            {


                "role":

                    "user",


                "content":

                    text


            }

        ],



        "temperature":

            0.6,



        "max_tokens":

            100,



        # Qwen3关闭thinking

        "chat_template_kwargs":

        {

            "enable_thinking":

                False

        }


    }





    response = requests.post(


        LLM_API,


        json=payload,


        timeout=120


    )



    response.raise_for_status()



    result = response.json()



    answer = (

        result

        ["choices"]

        [0]

        ["message"]

        ["content"]

        .strip()

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


        lang_code="zh",


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


    print(

        "Streaming interval:",

        f"{TTS_STREAMING_INTERVAL}s"

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


    try:


        results = tts_model.generate(

            text=text,

            voice=TTS_VOICE,

            lang_code="zh",

            max_tokens=1200,

            temperature=0.7,

            stream=True,

            streaming_interval=TTS_STREAMING_INTERVAL,

            verbose=False

        )


        for result in results:


            chunk_count += 1


            total_samples += result.samples


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


        if play_start is None and player.buffered_samples() > 0:


            play_start = now()


        player.wait_for_drain()


    finally:


        player.stop()


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
