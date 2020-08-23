FROM lizkes/ffmpeg_handbrake:1.0
WORKDIR /usr/local/vconvert/
COPY ./app/ ./app/
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
CMD python3 -m app.run