import crackn.settings as settings

indent = 13

def _generate_message(msg_type, text):
    spaces = ' ' * (indent - (len(msg_type) + 3)) # 3 is for the brackets and colon
    return f'[{msg_type}]:{spaces}{text}'

def _print_message(msg_type, text, urgency):
    if urgency >= settings.log_level:
        print(_generate_message(msg_type, text), flush=True)

def INFO(text, urgency=1):
    _print_message('INFO', text, urgency)

def WARNING(text, urgency=2):
    _print_message('WARNING', text, urgency)

def ERROR(text, urgency=3):
    _print_message('ERROR', text, urgency)