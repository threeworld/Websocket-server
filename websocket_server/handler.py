# -*- coding = utf-8 -*-

import re
import struct
import logging
from base64 import b64encode
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
        bytes = self.rfile.read(num)
        return map(ord, bytes)
    
    #握手
    def handshake(self):
        message = self.request.recv(20488).decode().strip()
        upgrade = re.search('\nupgrade[\s]*:[\s]*websocket', message.lower())
        if not upgrade:
            self.keep_alive = False
            return 
        key = re.search('\n[sS]ec-[wW]eb[sS]ocket-[kK]ey[\s]*:[\s]*(.*)\r\n', message)
        if key:
            key = key.group(1)
        else:
            logger.warning('Client tried to connect but was missing a key')
            self.keep_alive = True
            return 
        response = self.make_handshake_reponse(key)
        self.handshake_done = self.request.send(response.encode())
        self.valid_client = True
        self.server.new_client(self)
    #握手响应
    def make_handshake_reponse(self, key):
        return \
            'HTTP/1.1 101 Switching Protocols\r\n' \
            'Upgrade: websocket\r\n' \
            'Connection: Upgrade\r\n' \
            'Sec-WebSocket-Accept: %s\r\n' \
            '\r\n' % self.generate_response_key(key)

    #计算响应的key
    def generate_response_key(self, key):
        GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        hash = sha1(key.encode() + GUID.encode())
        response_key = b64encode(hash.digest()).strip()
        return response_key.decode('ASCII')

    #读消息
    def read_message(self):
        try:
            b1, b2 = self.read_bytes(2)
        except ValueError as e:
            b1, b2 = 0, 0
        fin = op_code.get('FIN')
        opcode = b1 & op_code.get('OPCODE')
        masked = b2 & op_code.get('MASKED')
        playload_len = b2 & op_code.get('PLAYLOAD_LEN')
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
