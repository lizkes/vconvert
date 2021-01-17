## Task json format
```jsonc
{
    "create_time": "191227174219",  //time_str %y%m%d%H%M%S
    "mode": "transcoding",          //transcoding mode
    "task_list": [
        [
            "/test/test.avi",       //path
            "normal",               //ttype
            "success"               //status
        ],
        [
            "/test/test2/test.ts",
            "dvd",
            "error"
        ],
        [
            "/test/test2/test2.iso",
            "iso",
            "running"
        ],
        [
            "/test/VIDEO_TS",
            "dvd-folder",
            "waiting"
        ]
    ]
}
```

