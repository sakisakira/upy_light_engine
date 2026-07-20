import os
import json
import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
from world import *

# reference: https://note.com/frenchbread/n/n9a46ada3850e
IsWeb = True
try:
    from js import window
except:
    IsWeb = False

class Savedata:
    TagTotal = "total"
    
    def __init__(self):
        self.filepath = False
        self.storage_item = False
        self.data = False

    def clear(self):
        self.data = {}
        
    def load(self):
        try:
            if IsWeb:
                self.storage_item = "bumping_rinder_savedata_" + g_world.Version
                data_str = window.localStorage.getItem(self.storage_item)
            else:
                if not self.filepath:
                    dir = "."        
                    self.filepath = dir + "savedata_" + g_world.Version
                    print(self.filepath)
                if not os.path.isfile(self.filepath):
                    self.data = {}
                    return
                with open(self.filepath, 'r') as f:
                    data_str = f.read()
            self.data = json.loads(data_str)
        except Exception:
            self.data = {}

    def save(self):
        try:
            data_str = json.dumps(self.data)
            if IsWeb:
                window.localStorage.setItem(self.storage_item, data_str)
            else:
                with open(self.filepath, 'w') as f:
                    f.write(data_str)
        except Exception as e:
            print(f"Exception {e}")

    def _time_tag(self, tag):
        return "time_" + str(tag)

    def _record_a_tag(self, tag):
        return "record_a_" + str(tag)

    def _record_b_tag(self, tag):
        return "record_b_" + str(tag)
    
    def set_time(self, tag, time):
        if not self.data: self.load()
        self.data[self._time_tag(tag)] = time

    def time(self, tag):
        if not self.data: self.load()
        return self.data.get(self._time_tag(tag), None)

    def set_record_a(self, tag, text):
        if not self.data: self.load()
        self.data[self._record_a_tag(tag)] = text

    def set_record_b(self, tag, text):
        if not self.data: self.load()        
        self.data[self._record_b_tag(tag)] = text

    def record_a(self, tag):
        if not self.data: self.load()        
        return self.data.get(self._record_a_tag(tag), None)

    def record_b(self, tag):
        if not self.data: self.load()        
        return self.data.get(self._record_b_tag(tag), None)

g_savedata = Savedata()
