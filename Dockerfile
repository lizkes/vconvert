FROM lizkes/ffmpeg_handbrake:latest
WORKDIR /vconvert_bin

ENV TZ=Asia/Shanghai
ENV LANG=C.UTF-8
COPY ./app /vconvert_bin/app
COPY ./fonts /usr/share/fonts/truetype
RUN apt-get update -y && apt-get install python3 python3-pip -y \
    && chmod 644 -R /usr/share/fonts/truetype && fc-cache && pip3 install chardet pyrebase \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
CMD python3 -m app.run