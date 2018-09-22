# -*- coding = utf-8 -*-

import re
import struct
import logging
from base64 import b64decode
from hashlib import sha1
from socketserver import StreamRequestHandler

from op_code import op_code

#日志设置
logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.INFO)

class WebSocketHandler(StreamRequestHandler):

    def __init__(self, socket, addr, server):
        self.server = server
        #继承StreamRequestHandler类
        StreamRequestHandler.__init__(self, socket, addr, server)

    #初始化
    def setup(self):
        StreamRequestHandler.setup(self)
        self.keep_alive = True
        self.handshake_done = False
        self.valid_client = False

    #实现handle方法
    def handle(self):
        while self.keep_alive:
            if not self.handshake_done:
                self.handshake()
            elif self.valid_client:
                self.read_message()
    
    #读字节
    def read_bytes(self, num):
        pass
    
    #握手
    def handshake(self):
        pass

    #握手响应
    def make_handshake_reponse(self, key):
        pass

    #计算响应的key
    def generate_response_key(self, key):
        pass
    
    #读消息
    def read_message(self):
        pass
    
    #发送消息
    def send_message(self, message, op_code):
        pass
    
    def send_pong(self, message, op_code):
        pass
    
    def send_text(self, message):
        pass
    
    def finish(self):
        pass
        
def encode_to_UTF8(data):
    pass

def decode_UTF8(data):
    pass