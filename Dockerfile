FROM lizkes/ffmpeg_handbrake:latest
WORKDIR /vconvert_bin

ENV TZ=Asia/Shanghai
ENV LANG=C.UTF-8
RUN apt-get update -y && apt-get install python3 tzdata -y \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && dpkg-reconfigure -f noninteractive tzdata
RUN apt-get install libfontconfig1-dev -y
COPY ./app /vconvert_bin/app
CMD python3 -m app.run