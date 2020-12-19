import os
import json

DIR = 'C:/DATA'
FILE = 'C:/DATA/data.txt'

data = {}

if not os.path.exists(DIR):
    os.mkdir(DIR)

if os.path.exists(FILE):
    with open(FILE,'r',encoding='UTF-8') as f:
        content = f.read()
        data = json.loads(content)

def set_key(key,value):
    data[key] = value
    with open(FILE,'w',encoding='UTF-8') as f:
        f.write(json.dumps(data))

def get_key(key,new_value=None):
    value = data.get(key)
    if value:
        return value
    if new_value:
        set_key(key,new_value)
        return new_value
    return value

