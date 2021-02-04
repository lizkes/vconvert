# ffmpeg转码工具

### 使用前提
需安装docker


### 使用方法
将下述指令的[input_dir]改为你想要转码的视频所在文件夹, 运行.
```bash
docker run -d \
    -v [input_dir]:/vconvert_input \
    lizkes/vconvert:latest
```

### 环境变量
可以添加各种环境变量来控制转码的行为
+ threads: 转码使用的线程数，默认为CPU核心数
+ mode: 运行模式，默认为transcoding，可选项 transcoding|burnsub|both
+ sleep_time: 休眠时间，默认为1800，单位为秒
+ remove_origin: 是否移除源文件，默认为false
+ remove_subtitle: 是否移除文件内的字幕, 默认为false
+ format: 设置转码后的文件格式，默认为mkv，可选项 mp4|mkv|webm
+ vc：设置转码后文件的视频编码，默认为h265，可选项 h264|h265|vp9
+ ac：设置转码后文件的音频编码，默认为aac，可选项 aac|opus
+ bit: 设置转码后文件的视频位数，默认为8，可选项 8|10
+ crf: 设置视频的质量，默认为20，越低越好
+ force_convert: 设置是否强制转码, 默认为false
+ fb_api_key: 设置firebase项目的网络API密钥, 默认为空，表示不启用
+ fb_project_id: 设置firebase项目的ID, 默认为空，表示不启用
+ fb_db_url: 设置firebase数据库的url, 默认为空，表示不启用
+ fb_email: 设置firebase验证的邮箱, 默认为空，表示不启用
+ fb_password: 设置firebase验证的密码, 默认为空，表示不启用
+ log_level: 设置docker日志的级别，默认为info，可选项 debug|info|warn|error|critical

### 示例
```bash
docker run --name vconvert -d \
    -v /download:/vconvert \
    -v /var/log/vconvert:/var/log/vconvert \
    -e "threads=8" \
    -e "remove_origin=true" \
    lizkes/vconvert:latest
```