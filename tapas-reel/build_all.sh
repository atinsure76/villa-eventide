#!/usr/bin/env bash
# Renders every version: full-quality master, standard MP4, and an iPhone/Instagram-ready copy.
set -e
cd "$(dirname "$0")"
mkdir -p out/iphone
render() { node render.mjs "$1" "out/master_$2.mp4" 30 > "out/log_$2.txt" 2>&1; }
render A        TheTapas_Reel_A_Destinations &
render B        TheTapas_Reel_B_2027ComingSoon &
render A:orange TheTapas_Reel_A_Destinations_Orange &
render B:orange TheTapas_Reel_B_2027ComingSoon_Orange &
wait
for f in TheTapas_Reel_A_Destinations TheTapas_Reel_B_2027ComingSoon TheTapas_Reel_A_Destinations_Orange TheTapas_Reel_B_2027ComingSoon_Orange; do
  ffmpeg -loglevel error -y -i "out/master_$f.mp4" -c:v libx264 -preset medium -crf 19 -maxrate 14M -bufsize 28M \
    -profile:v high -pix_fmt yuv420p -r 30 -movflags +faststart "out/$f.mp4" &
  ffmpeg -loglevel error -y -i "out/master_$f.mp4" -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 \
    -map 0:v -map 1:a -shortest -c:v libx264 -preset slow -profile:v high -level 4.1 -crf 21 -maxrate 6M -bufsize 12M \
    -pix_fmt yuv420p -r 30 -c:a aac -b:a 64k -tag:v avc1 -movflags +faststart "out/iphone/${f}_iPhone.mp4" &
done
wait
ls -la out/*.mp4 out/iphone/*.mp4
