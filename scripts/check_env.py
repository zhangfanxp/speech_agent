import platform
import subprocess


print("======================")
print("Speech Agent Check")
print("======================")


print(
    "System:",
    platform.platform()
)


print(
    "Machine:",
    platform.machine()
)



print("\nPython:")


subprocess.run(

    [
        "python",
        "--version"
    ]

)



print("\nMLX:")


subprocess.run(

    [
        "python",
        "-c",
        "import mlx;print(mlx.__version__)"
    ]

)


print("\nAudio devices:")


subprocess.run(

    [
        "python",
        "-c",
        "import sounddevice as sd;print(sd.query_devices())"
    ]

)
