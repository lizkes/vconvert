## Task json format
```json
{
    "create_time": "191227174219",  //time_str %y%m%d%H%M%S
    "task_list": [
        [
            "/test/test.avi",       //path
            "normal",               //task_type
            "success"               //task_status
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

