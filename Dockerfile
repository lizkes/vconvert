FROM lizkes/ffmpeg_handbrake:latest
WORKDIR /vconvert_bin

ENV TZ=Asia/Shanghai
ENV LANG=C.UTF-8
COPY ./app /vconvert_bin/app
COPY ./fonts /usr/share/fonts/truetype
RUN apt-get update -y && apt-get install python3 python3-pip tzdata -y \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && dpkg-reconfigure -f noninteractive tzdata
RUN apt-get install libfontconfig1-dev -y && chmod 644 -R /usr/share/fonts/truetype && fc-cache && pip3 install chardet
CMD python3 -m app.run