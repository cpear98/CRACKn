def init():
    global log_level
    log_level = 1

def set_silent(s):
    global log_level
    if s:
        log_level = 3