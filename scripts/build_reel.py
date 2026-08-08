import json, os, subprocess

def main():
    post_dir=open("latest_post_dir.txt",encoding="utf-8").read().strip()
    out=os.path.join(post_dir,"factbite_reel.mp4")
    # Five slides, 2.4s each, 1080x1920 vertical canvas. Audio is generated locally
    # by ffmpeg so this step adds no Gemini calls and does not use copyrighted music.
    inp=os.path.join(post_dir,"slides.txt")
    with open(inp,"w") as f:
        for i in range(1,6): f.write(f"file '{os.path.abspath(os.path.join(post_dir,f'slide_{i}.png'))}'\nduration 2.4\n")
        f.write(f"file '{os.path.abspath(os.path.join(post_dir,'slide_5.png'))}'\n")
    audio="sine=frequency=392:duration=12[s1];sine=frequency=494:duration=12[s2];sine=frequency=587:duration=12[s3];[s1][s2][s3]amix=inputs=3:duration=longest,volume=0.18"
    cmd=["ffmpeg","-y","-f","concat","-safe","0","-i",inp,"-f","lavfi","-i",audio,"-vf","scale=1080:1350:force_original_aspect_ratio=decrease,pad=1080:1920:0:285:color=black,format=yuv420p","-r","30","-t","12","-c:v","libx264","-preset","veryfast","-crf","27","-c:a","aac","-b:a","96k","-shortest",out]
    subprocess.run(cmd,check=True)
    os.remove(inp)
    print("Reel created:",out)
if __name__=="__main__": main()
