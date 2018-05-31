import os


def c_str(msg: str, color: str) -> str:
  if os.getenv('C', '1') == '0':
    return msg
  if color == 'RED':
    return '\033[{cv}{msg}\033[0m'.format(cv='31m', msg=msg)
  elif color == 'GREEN':
    return '\033[{cv}{msg}\033[0m'.format(cv='32m', msg=msg)
  elif color == 'YELLOW':
    return '\033[{cv}{msg}\033[0m'.format(cv='33m', msg=msg)
  elif color == 'CYAN':
    return '\033[{cv}{msg}\033[0m'.format(cv='36m', msg=msg)
  elif color == 'WHITE':
    return '\033[{cv}{msg}\033[0m'.format(cv='37m', msg=msg)
