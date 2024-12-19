import re
import time

def gstrb(from_str, to_str, strs, offset=0):
    offset_start = (strs.find(from_str, offset) + len(from_str)) if (offset_start := strs.find(from_str, offset)) != -1 else offset
    offset_end = strs.find(to_str, offset_start) if (offset_end := strs.find(to_str, offset_start)) != -1 else len(strs)
    return strs[offset_start:offset_end]

def get_sign(num):
    return 'negative' if num < 0 else 'zero' if num == 0 else 'positive'

def format_strtime(time, suff={}):
    h, remainder = divmod(time, 3600)
    m, s = divmod(remainder, 60)
    return ' '.join(f"{val}{unit}" for val, unit in ((h, suff.get('h', 'H')), (m, suff.get('m', 'M')), (s, suff.get('s', 'sec'))) if val)

def get_time_next(seconds):
    ft = int(time.time()) + seconds
    left = ft % 60
    return ft - left if left < 30 else ft + (60 - left)

def strip_ansi(text):
    # Strip ANSI color codes from a string
    return re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', text)

def file_get_contents(filename):
    try: return open(filename, 'r', newline='', encoding='utf-8').read()
    except FileNotFoundError: return ''

def file_put_contents(filename, content, mode='w'):
    try: open(filename, mode, newline='', encoding='utf-8').write(content); return len (content)
    except IOError: return False