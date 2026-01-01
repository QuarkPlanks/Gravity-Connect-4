# network.py
import socket
import threading
import json
import time

# 默认端口
DEFAULT_PORT = 12345
# 缓冲区大小
BUFFER_SIZE = 4096

class NetworkManager:
    def __init__(self):
        self.socket = None
        self.is_host = False
        self.connected = False
        self.running = False
        
        # 消息队列：存放收到的指令，供GUI在主线程取出执行
        self.msg_queue = []
        
        # 自身角色 (1 or 2, 1 usually goes first)
        self.my_id = 0 
        
        # 线程锁，防止多线程同时操作 socket 导致冲突
        self.lock = threading.Lock()

    def get_local_ip(self):
        """获取本机在局域网中的IP地址 (黑科技写法)"""
        try:
            # 利用 UDP 连接 Google DNS (并没有真的发送数据) 来判断本机 IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start_host(self, port=DEFAULT_PORT):
        """启动服务器（房主）"""
        self.is_host = True
        self.running = True
        
        try:
            # TODO 1: 创建 TCP Socket (AF_INET, SOCK_STREAM)
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 允许端口复用 (防止频繁重启显示端口被占用)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # TODO 2: 绑定 IP 和 端口 ('0.0.0.0', port)
            self.server_socket.bind(('0.0.0.0', port))
            
            # TODO 3: 开始监听，最大连接数设为 1
            self.server_socket.listen(1)
            
            # 开启线程等待连接，避免卡死主界面
            threading.Thread(target=self._accept_client, daemon=True).start()
            return True, self.get_local_ip()
        except Exception as e:
            return False, str(e)

    def _accept_client(self):
        """等待客户端连接 (在子线程运行)"""
        try:
            # TODO: 调用 accept() 阻塞等待
            connection, addr = self.server_socket.accept()
            print(f"[Network] Client connected from {addr}")
            
            with self.lock:
                self.socket = connection
                self.connected = True
            
            # 开启接收数据的循环线程
            threading.Thread(target=self._receive_loop, daemon=True).start()
            
            # 通知 UI 有人连上了
            self.msg_queue.append({"type": "SYS_CONNECTED", "addr": addr})
            
        except Exception as e:
            print(f"[Network] Accept Error: {e}")

    def start_client(self, ip, port=DEFAULT_PORT):
        """连接服务器（加入者）"""
        self.is_host = False
        self.running = True
        
        try:
            # TODO 1: 创建 TCP Socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 设置连接超时
            self.socket.settimeout(5) 
            
            # TODO 2: 连接服务器 (ip, port)
            self.socket.connect((ip, port))
            self.socket.settimeout(None)
            
            with self.lock:
                self.connected = True
            
            # 开启接收线程
            threading.Thread(target=self._receive_loop, daemon=True).start()
            return True, "Connected"
        except Exception as e:
            return False, str(e)

    def _receive_loop(self):
        """持续接收数据的循环 (子线程)"""
        buffer = ""
        while self.running and self.connected:
            try:
                # TODO 1: 接收数据 self.socket.recv
                data = self.socket.recv(BUFFER_SIZE)
                
                if not data:
                    break # 连接断开
                
                # 处理粘包问题 (TCP是流式协议，通过换行符来切分 JSON)
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    msg_str, buffer = buffer.split('\n', 1)
                    if msg_str.strip():
                        try:
                            # TODO 2: 将字符串 parse 为 json 对象
                            msg_obj = json.loads(msg_str)
                            # TODO 3: 存入 self.msg_queue
                            self.msg_queue.append(msg_obj)
                        except json.JSONDecodeError:
                            pass
                            
            except Exception as e:
                print(f"[Network] Recv Error: {e}")
                break
        
        self._handle_disconnect()

    def _handle_disconnect(self):
        with self.lock:
            if self.connected:
                self.connected = False
                self.msg_queue.append({"type": "SYS_DISCONNECTED"})
                if self.socket:
                    self.socket.close()

    def send(self, data_dict):
        """发送字典数据 (自动转JSON)"""
        if not self.connected or not self.socket:
            return
        
        try:
            # TODO: 将字典转为 json 字符串，并加上换行符 '\n' (这是我们的协议)
            msg = json.dumps(data_dict) + '\n'
            # TODO: 发送编码后的 bytes
            self.socket.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"[Network] Send Error: {e}")
            self._handle_disconnect()

    def close(self):
        """关闭网络模块"""
        self.running = False
        self.connected = False
        if self.socket:
            try: self.socket.close()
            except: pass
        if self.is_host and hasattr(self, 'server_socket'):
            try: self.server_socket.close()
            except: pass

    def pop_msg(self):
        """从队列取出一个消息 (供主线程调用)"""
        if self.msg_queue:
            return self.msg_queue.pop(0)
        return None