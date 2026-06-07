import os
import subprocess


def compose(image_paths, audio_paths, out_path):
    """One ffmpeg-rendered clip per scene (image + its audio), then concat.
    ffmpeg is always real — it is deterministic local composition, not a model.
    ffmpeg must be installed in the worker image (apt-get install -y ffmpeg).
    """
    work = os.path.dirname(out_path)
    clips = []
    for i, (img, aud) in enumerate(zip(image_paths, audio_paths)):
        clip = os.path.join(work, f"clip{i}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", img, "-i", aud,
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", clip,
        ], check=True)
        clips.append(clip)

    listfile = os.path.join(work, "concat.txt")
    with open(listfile, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
        "-c", "copy", out_path,
    ], check=True)
    return out_path
