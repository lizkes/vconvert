FROM python:slim
COPY ./app /usr/local/vconvert/
WORKDIR /usr/local/vconvert/
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone &&\
    apt-get update
CMD python run.py