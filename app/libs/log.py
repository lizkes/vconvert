import logging

def pfatal(s: str):
    logging.fatal(s)
    print(s)

def perror(s: str):
    logging.error(s)
    print(s)

def pwarn(s: str):
    logging.warn(s)
    print(s)

def pinfo(s: str):
    logging.info(s)
    print(s)
    
def pdebug(s: str):
    logging.debug(s)
    print(s)