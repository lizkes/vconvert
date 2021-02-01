## Task json format
```jsonc
{
    "activate_time": "191227174219",  //time_str %y%m%d%H%M%S
    "mode": "transcoding",          //mode
    "status": "done",               //status
    "task_list": [
        [
            "/test/test.avi",       //path
            "normal",               //ttype
            "done",               //status
            "6ebbadfc06424595821e959a3fa71a9c",  //uuid
        ],
        [
            "/test/test2/test.ts",
            "dvd",
            "error",
            "6ebbadfc06424595821e959a3fa71a9c",  //uuid
        ],
        [
            "/test/test2/test2.iso",
            "iso",
            "running",
            "6ebbadfc06424595821e959a3fa71a9c",  //uuid
        ],
        [
            "/test/VIDEO_TS",
            "dvd-folder",
            "waiting",
            "6ebbadfc06424595821e959a3fa71a9c",  //uuid
        ]
    ]
}
```

