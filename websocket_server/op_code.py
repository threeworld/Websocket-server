# -*- coding='utf-8' -*-

op_code = {
    'FIN' : 0x80,
    'OPCODE' : 0x0f,
    'MASK' : 0x80,
    'PAYLOAD_LEN' : 0x7f, # 0111 1111
    'PAYLOAD_LEN_EXT16' : 0x7e, # 126
    'PAYLOAD_LEN_EXT64' : 0x7f, # 127
    'OPCODE_CONTINUATION' : 0x00, #中间数据包
    'OPCODE_TEXT' : 0x01,  #标识一个text类数据包
    'OPCODE_BINARY' : 0x02,  #标识一个binary类型数据包 
    'OPCODE_CLOSE' : 0x08, #标识一个断开连接类型数据包
    'OPCODE_PING' : 0x09, #标识一个ping数据包
    'OPCODE_PONG' : 0xA   #表示一个pong类型数据包
}