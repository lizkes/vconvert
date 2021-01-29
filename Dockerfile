FROM lizkes/ffmpeg_handbrake:latest
WORKDIR /vconvert

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt-get update -y && apt-get install python3 -y
COPY ./app /vconvert/app
CMD python3 -m app.run