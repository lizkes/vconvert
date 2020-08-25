# 转码任意视频

### 使用前提
需安装docker


### 使用方法
将下述指令的[input_dir]改为你想要转码的视频所在文件夹, [log_dir]改为你想要存储日志的文件夹, 运行.
```bash
docker run -v [input_dir]:/vconvert_input -v [log_dir]:/usr/local/vconvert/app/logs/ -d lizkes/vconvert:latest
```

### 环境变量
可以添加各种环境变量来控制转码的行为
+ threads: 转码使用的线程数，默认为CPU核心数
+ remove_source: 是否移除源文件，默认为False
+ remove_subtitle: 是否移除源文件内的字幕, 默认为False
+ format: 设置转码后的文件格式，默认为mp4，可选项 mp4|mkv|webm
+ vc：设置转码后文件的视频编码，默认为h264，可选项 h264|h265|vp9
+ ac：设置转码后文件的音频编码，默认为aac，可选项 aac|opus
+ bit: 设置转码后文件的视频位数，默认为8，可选项 8|10
+ log_level: 设置docker日志的级别，默认为info，可选项 debug|info|warn|error|critical

### 示例
```bash
docker run --name vconvert -d \
    -v /usr/local/transmission/download:/vconvert_input \
    -v /var/log/vconvert/:/usr/local/vconvert/app/logs/ \
    -e "threads=8" \
    -e "remove_source=True" \
    lizkes/vconvert:latest
```