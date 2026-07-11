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



from config import (

    LLM_API,

    LLM_MODEL,


    ASR_MODEL,


    TTS_MODEL,

    TTS_VOICE,


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
# 加载模型
# =====================================


print("加载 Silero VAD...")


vad_model = load_silero_vad()



print("加载 Whisper...")


asr_model = load_asr_model(

    ASR_MODEL

)



print("加载 Qwen3-TTS...")


tts_model = load_tts_model(

    TTS_MODEL

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

# =====================================
# ASR 语音识别
# =====================================


def speech_to_text():


    print(

        "📝 正在识别..."

    )



    result = asr_model.generate(

        "input.wav"

    )



    text = result.text.strip()



    print(

        "用户:",

        text

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



    return answer






# =====================================
# TTS语音合成
# =====================================


def text_to_speech(text):


    print(

        "🔊 生成语音..."

    )



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



    return output_file






# =====================================
# 播放音频
# =====================================


def play_audio(file):


    print(

        "▶ 播放:",

        file

    )



    subprocess.run(

        [

            "afplay",

            file

        ]

    )






# =====================================
# 主程序
# =====================================


def main():


    while True:


        try:



            # 等待讲话

            record_audio_vad()



            # ASR

            text = speech_to_text()



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



                audio = text_to_speech(

                    goodbye

                )


                play_audio(

                    audio

                )



                print(

                    "\n退出 Voice Agent"

                )



                break





            # ==========================
            # 正常对话
            # ==========================


            answer = chat(text)



            if answer:


                audio = text_to_speech(

                    answer

                )


                play_audio(

                    audio

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

