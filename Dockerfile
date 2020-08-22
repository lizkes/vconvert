FROM python:slim
COPY ./app/ /usr/local/vconvert/app/
COPY ./bin/ /usr/local/bin/
WORKDIR /usr/local/vconvert/
ENV TZ=Asia/Shanghai
ENV PATH="$PATH:/usr/local/bin"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone &&\
    apt-get update
CMD python -m app.run