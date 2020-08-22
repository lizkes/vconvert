FROM python:slim
COPY ./app/ /usr/local/vconvert/app/
COPY ./bin/ /usr/local/bin/
WORKDIR /usr/local/vconvert/
ENV TZ=Asia/Shanghai PATH=usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone &&\
    apt-get update &&\
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe /usr/local/bin/HandBrakeCLI
CMD python -m app.run