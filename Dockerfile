FROM debian:stable-slim
WORKDIR /usr/local/vconvert/
COPY ./app/ ./app/
COPY ./ffmpeg_build_script.sh ./build/ffmpeg/ffmpeg_build_script.sh
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone &&\
    apt-get update &&\
    apt-get -y install autoconf automake build-essential cmake git libass-dev libbz2-dev libfontconfig1-dev libfreetype6-dev libfribidi-dev libharfbuzz-dev libjansson-dev liblzma-dev libmp3lame-dev libnuma-dev libogg-dev libopus-dev libsamplerate-dev libspeex-dev libtheora-dev libtool libtool-bin libturbojpeg0-dev libvorbis-dev libx264-dev libxml2-dev libvpx-dev m4 make meson nasm ninja-build patch pkg-config tar zlib1g-dev &&\
    cd ./build/ && git clone https://github.com/HandBrake/HandBrake.git && cd HandBrake && ./configure --launch-jobs=$(nproc) --launch --disable-gtk && mv ./build/HandBrakeCLI /usr/local/bin/HandBrakeCLI && cd ../ && rm -rf HandBrake &&\
    cd ./ffmpeg && /bin/bash ./ffmpeg_build_script.sh --build && cd ../../ && rm -rf build &&\
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe /usr/local/bin/HandBrakeCLI
CMD python3 -m app.run