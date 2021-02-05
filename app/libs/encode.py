import chardet
import logging


def is_utf16(input_file):
    with open(input_file, "rb") as f:
        rawdata = f.read()
        result = chardet.detect(rawdata)
        return result["encoding"] == "UTF-16"


def utf16_to_utf8(input_file, output_file):
    try:
        with open(input_file, "r", encoding="utf-16") as f1:
            content = f1.read()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f2:
            f2.write(content)
    except UnicodeDecodeError:
        logging.error(f"utf-16 decode error: {input_file.as_posix()}")
