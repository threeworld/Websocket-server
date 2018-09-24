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
        return bytes
    
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
            b1, b2 = self.read_bytes(2)  # b1，b2分别对应客户端数据前两个字节
        except ValueError as e:
            b1, b2 = 0, 0
        #通过&操作获取对应的bit    
        fin = op_code.get('FIN')
        opcode = b1 & op_code.get('OPCODE')  #断开opcode
        masked = b2 & op_code.get('MASKED')
        payload_len = b2 & op_code.get('PAYLOAD_LEN')
        
        if not b1:
            logger.info('Client closed connection')
            return
        if opcode == op_code.get('OPCODE_CLOSE'):
            logger.info('Client asked to close connection')
            self.keep_alive = False
            return 
        #没有掩码处理
        if not masked:
            logger.error('Client must always be masked')
            self.keep_alive = False
            return
        if opcode == op_code.get('OPCODE_CONTINUATION'):
            logger.warn('Continuation frames are not supported.')
            return 
        if opcode == op_code.get('OPCODE_BINARY'):
            logger.warn('Binary frames are not supported.')
            return 
        elif opcode == op_code.get('OPCODE_TEXT'):
            opcode_handler = self.server.message_received
        elif opcode == op_code.get('OPCODE_PING'):
            opcode_handler = self.server.ping_received
        elif opcode == op_code.get('OPCODE_PONG'):
            logger.warn('pong frames are not supported. ')
            return
        else:
            logger.warn("Unknown opcode %#x." + opcode)
            self.keep_alive = False
            return
        
        if payload_len == 126:
            payload_len = struct.unpack('>H', self.rfile.read(2))[0]
        elif payload_len == 127:
            payload_len = struct.unpack('>Q', self.rfile.read(8))[0]    
        
        masks = self.read_bytes(4)
        message_bytes = bytearray()
        for message_byte in self.read_bytes(payload_len):
            message_byte ^= masks[len(message_bytes) % 4]
            message_bytes.append(message_byte)
        opcode_handler(self, message_bytes.decode('utf8'))

    #发送消息
    def send_message(self, message):
        self.send_text(message)
    
    def send_pong(self, message, op_code):
        self.send_text(message, op_code.get('OPCODE_PONG'))
    
    def send_text(self, message, opcode=op_code.get('OPCODE_TEXT')):
        if isinstance(message, bytes):
            message = decode_to_UTF8(message)
            if not message:
                logger.error('Can\'t send message, message is not valid UTF-8')
                return False
        elif isinstance(message, str):
            pass
        else:
            logger.error('Can\'t send message, message has to be a string or bytes. Given type is %s' % type(message))
            return
        
        header = bytearray()
        payload = encode_to_UTF8(message)
        payload_len = len(payload)

        if payload_len <= 125:
            header.append(op_code.get('FIN') | opcode)
            header.append(payload_len)

        elif payload_len > 125 and payload_len <= 65535:
            header.append(op_code.get('FIN') | opcode)
            header.append(op_code.get('pAYLOAD_LEN_EXT16'))
            header.extend(struct.pack('>H', payload_len))

        elif payload_len < 18446744073709551616:
            header.append(op_code.get('FIN') | opcode)
            header.append(op_code.get('pAYLOAD_LEN_EXT64'))
            header.extend(struct.pack('>Q', payload_len))
    
        else:
            raise Exception('Message is too big. Consider breaking it into chunks.')
            return

        self.request.send(header + payload)
    
    def finish(self):
        self.server.client_left(self)
        
def encode_to_UTF8(data):
    try:
        return data.encode('UTF-8')
    except UnicodeEncodeError as e:
        logger.error('Could not encode data to UTF-8 -- %s' % e)
    except Exception as e:
        raise(e)
        return False

def decode_to_UTF8(data):
    try:
        return data.decode('UTF-8')
    except UnicodeEncodeError as e:
        logger.error('Could not decode data to UTF-8 -- %s' % e)
    except Exception as e:
        raise(e)
        return False