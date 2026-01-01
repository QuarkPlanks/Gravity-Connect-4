# gui.py
import pygame
import sys
import time
import threading
import random
import re
# 引入核心模块
from match import Match
from ai import AIPlayer
import storage
import network

# --- 配置常量 ---
WINDOW_WIDTH = 1000 
WINDOW_HEIGHT = 800
FPS = 60
MIN_WIDTH = 800
MIN_HEIGHT = 600

# 颜色定义
COLOR_BG = (245, 245, 245)
COLOR_BOARD = (50, 60, 80)
COLOR_EMPTY = (230, 230, 230)
COLOR_P1 = (231, 76, 60)        # Red
COLOR_P2 = (241, 196, 15)       # Yellow
COLOR_BLOCK = (44, 62, 80)      # Obstacle
COLOR_HOVER = (255, 255, 255, 50)
COLOR_TEXT = (50, 50, 50)
COLOR_BTN = (52, 152, 219)
COLOR_BTN_HOVER = (41, 128, 185)
COLOR_BTN_RED = (231, 76, 60)
COLOR_BTN_GRAY = (149, 165, 166)
COLOR_BTN_GREEN = (46, 204, 113)
COLOR_INPUT_ACTIVE = (220, 230, 240)
COLOR_LIST_SEL = (210, 230, 255)

class GameGUI:
    def __init__(self):
        # TODO 1: Pygame 初始化
        # 初始化 pygame, screen, clock, fonts (title, mid, small)
        # 设置窗口 caption
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Gravity Connect 4 - Ultimate Edition")
        self.clock = pygame.time.Clock()
        
        self.font_title = pygame.font.SysFont("Arial", 50, bold=True)
        self.font_mid = pygame.font.SysFont("Arial", 26)
        self.font_small = pygame.font.SysFont("Arial", 20)

        # --- 状态机定义 ---
        # 包含: MAIN, NEW_GAME, PLAYING, PLAYING_AIvAI, ANIMATING, GAMEOVER,
        #       SAVES, REVIEWS, REVIEW_PLAYING,
        #       NET_SELECT, NET_HOST_WAIT, NET_JOIN_INPUT, NET_JOIN_WAIT
        self.state = "MAIN" 
        
        # 核心对象
        self.match = None
        self.network = network.NetworkManager()
        
        # 游戏配置 (默认值)
        self.N = 8 
        self.game_mode = "PvP"
        self.is_online = False
        self.difficulty_1 = "Medium"
        self.difficulty_2 = "Medium"
        self.num_obstacles = 3
        self.use_timer = True      
        self.time_limit_val = 30   
        
        # 运行时数据
        self.turn = 1
        self.winner = None
        self.timer_start = 0
        self.time_left = 0
        
        # AI 相关
        self.ai_p1 = None
        self.ai_p2 = None
        self.ai_thinking = False
        self.ai_pending_move = None
        self.ai_delay_start = 0

        # UI 交互状态 (输入框、文件列表)
        self.input_text = ""        # 通用文本缓冲
        self.input_obs = "3"        # 障碍物输入缓冲
        self.input_time = "30"      # 时间输入缓冲
        self.active_input = "TEXT"  # 当前激活的输入框: "TEXT", "OBS", "TIME"
        
        self.selected_file_idx = -1
        self.file_list = []
        self.click_event = False 
        
        # 布局与动画
        self.board_rect = None
        self.cell_size = 0
        self.anim_piece = None # 字典: {x, y, target_y, velocity, col, player}
        
        # 回放数据
        self.review_data = None
        self.review_step = 0
        self.review_moves = []
        
        # 弹窗与网络辅助
        self.popup = None 
        self.net_ip = "127.0.0.1"
        self.net_msg = ""
        self.pending_load_data = None # 用于联机加载存档的临时存储

    # ================= 辅助方法 =================
    
    def reset_ui_state(self):
        """重置所有 UI 输入框和列表状态"""
        # TODO: 将 input_text, input_obs, input_time 等重置为默认值
        # 清空 file_list, popup 等
        self.input_text = ""
        self.input_obs = "3"
        self.input_time = "30"
        self.active_input = "TEXT"
        self.selected_file_idx = -1
        self.file_list = []
        self.popup = None
        self.net_msg = ""

    def show_popup(self, msg, type="ALERT", callback=None, no_callback=None):
        """显示弹窗"""
        # TODO: 设置 self.popup 字典
        self.popup = {'msg': msg, 'type': type, 'callback': callback, 'no_callback': no_callback}

    # ================= 游戏初始化逻辑 =================

    def init_game(self, n=8, mode="PvP", load_data=None, num_obstacles=3, is_online=False, use_timer=True, time_limit=30):
        """
        初始化一局新游戏。
        支持从 load_data (读档) 恢复，或者创建全新的 Match。
        """
        # TODO 1: 更新配置变量 (self.N, self.game_mode, self.is_online 等)
        self.N = n
        self.game_mode = mode
        self.is_online = is_online
        self.num_obstacles = num_obstacles
        self.use_timer = use_timer
        self.time_limit_val = time_limit

        # TODO 2: Match 初始化
        # if load_data:
        #    从 Match.from_dict 恢复 self.match
        #    恢复 self.turn, self.time_left
        #    如果是单机读档，覆盖 mode, difficulty 等设置
        # else:
        #    根据 is_online 和 is_host 判断是否需要生成障碍物
        #    self.match = Match(n, ...)
        if load_data:
            self.match = Match.from_dict(load_data['match'])
            self.turn = load_data.get('turn', 1)
            self.time_left = load_data.get('time_left', 30)
            if not is_online: # 只有单机才覆盖配置
                self.game_mode = load_data.get('game_mode', 'PvP')
                self.difficulty_1 = load_data.get('difficulty_1', 'Medium')
                self.difficulty_2 = load_data.get('difficulty_2', 'Medium')
                self.use_timer = load_data.get('use_timer', True)
                self.time_limit_val = load_data.get('time_limit_val', 30)
        else:
            if is_online and not self.network.is_host:
                self.match = Match(n, num_obstacles=0) # 客机不生成障碍，等主机发
            else:
                self.match = Match(n, num_obstacles=num_obstacles)
            self.turn = 1
            self.time_left = self.time_limit_val
        
        # TODO 3: 计时器与 AI 初始化
        # self.timer_start = time.time()
        # 根据 mode 初始化 self.ai_p1, self.ai_p2 (PvAI 或 AIvAI)
        self.timer_start = time.time() - (self.time_limit_val - self.time_left)
        self.winner = None
        self.ai_thinking = False
        self.ai_p1, self.ai_p2 = None, None

        if not is_online:
            if mode == "PvAI": self.ai_p2 = AIPlayer(self.difficulty_1)
            elif mode == "AIvAI":
                self.ai_p1 = AIPlayer(self.difficulty_1)
                self.ai_p2 = AIPlayer(self.difficulty_2)

        # TODO 4: 布局与状态切换
        # 调用 self.resize_layout()
        # 如果是 AIvAI -> state="PLAYING_AIvAI", 否则 "PLAYING"
        self.resize_layout()
        self.state = "PLAYING_AIvAI" if mode == "AIvAI" else "PLAYING"
        
        # TODO 5: 联机同步 (仅 Host)
        # if is_online and is_host:
        #    调用 self.send_game_init()
        if is_online and self.network.is_host:
            self.send_game_init()

    def send_game_init(self):
        """(Host专用) 发送初始盘面给 Client"""
        # TODO: 构造 INIT 数据包 (包含 N, board, obstacles, turn 等)
        # 调用 self.network.send(packet)
        # 随机分配先手后手: send "START" 包通知 Client 它的 ID
        packet = {
            "type": "INIT",
            "N": self.N,
            "board_matrix": self.match.board,
            "use_timer": self.use_timer,
            "time_limit": self.time_limit_val,
            "turn": self.turn,
            "time_left": self.time_left
        }
        self.network.send(packet)
        # 随机分配，host 如果是 1，则 client 是 2
        host_id = 1 if self.match.history else random.randint(1, 2) # 读档时P1默认Host
        self.network.my_id = host_id
        self.network.send({"type": "START", "your_id": 3 - host_id})

    # ================= 核心 Update 循环 =================

    def update(self):
        """主逻辑更新：每一帧调用"""
        if self.popup: return
        current_time = time.time()

        # 1. 网络消息处理
        if self.is_online or self.state.startswith("NET"):
            self.process_network_messages()

        # 2. 正常游戏状态 (PLAYING)
        if self.state == "PLAYING":
            # TODO: 联机轮次检查 (如果是联机且不是我的回合，return)
            if self.is_online and (self.turn != self.network.my_id or self.network.my_id == 0):
                pass # 不能动
            
            # TODO: PvAI 逻辑
            # 如果是 PvAI 且轮到 AI (turn==2) 且 !online:
            #    启动 AI 线程 (参考 run_ai_thread)
            #    检查 ai_pending_move，如果有值 -> attempt_move(col)
            elif self.game_mode == "PvAI" and self.turn == 2 and not self.is_online:
                if not self.ai_thinking and self.ai_pending_move is None:
                    self.ai_thinking = True
                    threading.Thread(target=self.run_ai_thread, args=(2,), daemon=True).start()
                if self.ai_pending_move is not None:
                    col = self.ai_pending_move
                    self.ai_pending_move = None
                    self.ai_thinking = False
                    if col is not None: self.attempt_move(col)

            # TODO: 倒计时逻辑
            # if use_timer: 更新 time_left
            # 如果超时 -> switch_turn_logic()
            if self.use_timer and not self.winner:
                elapsed = current_time - self.timer_start
                self.time_left = max(0, self.time_limit_val - elapsed)
                if self.time_left <= 0: self.switch_turn_logic()

        # 3. AI 对战 AI 状态
        elif self.state == "PLAYING_AIvAI":
            # TODO: 双 AI 自动对弈逻辑
            # 增加随机延迟 (delay)，让 AI 下棋不要太快
            # 轮流调用 run_ai_thread
            if not self.winner:
                if not self.ai_thinking and self.ai_pending_move is None:
                    if self.ai_delay_start == 0: self.ai_delay_start = current_time
                    if current_time - self.ai_delay_start > random.uniform(0.3, 0.8):
                        self.ai_thinking = True
                        threading.Thread(target=self.run_ai_thread, args=(self.turn,), daemon=True).start()
                
                if self.ai_pending_move is not None:
                    col = self.ai_pending_move
                    self.ai_pending_move = None
                    self.ai_thinking = False
                    self.ai_delay_start = 0
                    if col is not None: self.attempt_move(col)
                
                if self.use_timer:
                    self.time_left = max(0, self.time_limit_val - (current_time - self.timer_start))

        # 4. 动画状态 (重点)
        elif self.state == "ANIMATING":
            # TODO: 物理掉落逻辑
            # p = self.anim_piece
            # p['velocity'] += 重力加速度 (如 2)
            # p['y'] += p['velocity']
            # if p['y'] >= p['target_y']:
            #     修正 p['y'] = p['target_y']
            #     调用 self.match.move(...) 真正落子
            #     调用 self.finish_move()
            if self.anim_piece:
                p = self.anim_piece
                p['velocity'] += 2
                p['y'] += p['velocity']
                if p['y'] >= p['target_y']:
                    p['y'] = p['target_y']
                    self.match.move(p['col'], p['player'])
                    self.finish_move()

    def process_network_messages(self):
        """处理网络队列中的消息"""
        while True:
            msg = self.network.pop_msg()
            if not msg: break
            
            # TODO: 处理各类消息
            # SYS_CONNECTED: 连接成功 -> 根据状态跳转 (Host发Init, Client等Init)
            # INIT: Client收到初始化包 -> init_game(...)
            # START: 收到自己的 ID -> self.network.my_id = ...
            # MOVE: 收到对手落子 -> attempt_move(col, from_network=True)
            # SURRENDER: 对手投降 -> winner=my_id, state=GAMEOVER
            # SYS_DISCONNECTED: 调用 handle_disconnect()
            mtype = msg.get("type")
            if mtype == "SYS_CONNECTED":
                if self.state == "NET_HOST_WAIT":
                    if self.pending_load_data:
                        self.init_game(n=8, mode="PvP", load_data=self.pending_load_data, is_online=True)
                        self.pending_load_data = None
                    else:
                        self.init_game(self.N, self.game_mode, num_obstacles=self.num_obstacles, is_online=True, 
                                       use_timer=self.use_timer, time_limit=self.time_limit_val)
            elif mtype == "SYS_DISCONNECTED":
                self.handle_disconnect()
            elif mtype == "INIT":
                self.init_game(msg.get("N", 8), "PvP", is_online=True, 
                               use_timer=msg.get("use_timer", True), time_limit=msg.get("time_limit", 30))
                # 覆盖 board
                if msg.get("board_matrix"): self.match.board = msg["board_matrix"]
                self.turn = msg.get("turn", 1)
                self.time_left = msg.get("time_left", 30)
                self.state = "PLAYING"
            elif mtype == "START":
                self.network.my_id = msg.get("your_id")
            elif mtype == "MOVE":
                if msg.get("player") != self.network.my_id:
                    self.attempt_move(msg.get("col"), from_network=True)
            elif mtype == "SURRENDER":
                self.winner = self.network.my_id
                self.state = "GAMEOVER"

    def handle_disconnect(self):
        """处理断线"""
        # TODO: 弹窗提示，并询问是否保存游戏
        if self.state in ["PLAYING", "ANIMATING", "GAMEOVER"]:
            self.state = "GAMEOVER"
            def save_quit():
                self.popup = None
                self.state = "DIALOG_SAVE"
                self.input_text = f"disconnect_{int(time.time())%1000}"
                self.network.close()
                self.is_online = False
            def just_quit():
                self.popup = None
                self.state = "MAIN"
                self.network.close()
                self.is_online = False
            self.show_popup("Opponent Disconnected!\nSave Game?", "CONFIRM", save_quit, just_quit)
        else:
            self.network.close()
            self.is_online = False
            self.show_popup("Connection Lost", "ALERT", lambda: setattr(self, 'state', 'MAIN'))

    def run_ai_thread(self, player_id):
        """AI 子线程入口"""
        # TODO: 获取对应 AI 对象 -> 调用 get_best_move -> 存入 self.ai_pending_move
        ai = self.ai_p1 if player_id == 1 else self.ai_p2
        move = ai.get_best_move(self.match, player_id)
        self.ai_pending_move = move

    # ================= 落子与动画逻辑 =================

    def attempt_move(self, col, from_network=False):
        """
        尝试落子：并不直接修改棋盘，而是初始化动画状态。
        """
        # TODO 1: 合法性校验
        # 如果是联机且不是我的回合(且非网络包)，返回
        if self.is_online and not from_network:
            if self.turn != self.network.my_id or self.network.my_id == 0: return

        # TODO 2: 获取落点行号
        # target_row = self.match.get_target_row(col)
        # if target_row == -1: return
        target_row = self.match.get_target_row(col)
        if target_row == -1: return

        # TODO 3: 发送网络包 (如果是本地操作且联机)
        if self.is_online and not from_network:
            self.network.send({"type": "MOVE", "col": col, "player": self.turn})
        
        # TODO 4: 初始化动画数据 (关键)
        # self.state = "ANIMATING"
        # start_y = 棋盘上方
        # target_y_px = 目标行的像素坐标
        # self.anim_piece = {'col': col, 'row': target_row, 'x': ..., 'y': start_y, 'target_y': target_y_px, 'player': self.turn, 'velocity': 0}
        self.state = "ANIMATING"
        start_y = self.board_rect.y - self.cell_size
        target_y = self.board_rect.y + target_row * self.cell_size
        self.anim_piece = {
            'col': col, 'row': target_row, 
            'x': self.board_rect.x + col * self.cell_size, 
            'y': start_y, 'target_y': target_y, 
            'player': self.turn, 'velocity': 0
        }

    def finish_move(self):
        """动画结束后的结算"""
        self.anim_piece = None
        # TODO: 判断胜负
        # is_over, winner, _ = self.match.judge()
        # if is_over: state = GAMEOVER
        # else: switch_turn_logic()
        is_over, winner, _ = self.match.judge()
        if is_over:
            self.winner = winner
            self.state = "GAMEOVER"
        else:
            self.switch_turn_logic()

    def switch_turn_logic(self):
        """切换回合与重置计时"""
        # self.turn = 3 - self.turn
        # 重置 timer_start
        # 切换状态回 PLAYING 或 PLAYING_AIvAI
        self.turn = 3 - self.turn
        self.timer_start = time.time()
        self.time_left = self.time_limit_val
        self.state = "PLAYING_AIvAI" if self.game_mode == "AIvAI" else "PLAYING"

    # ================= 界面绘制与交互 =================

    def resize_layout(self):
        """响应窗口大小调整，计算棋盘尺寸"""
        # TODO: 根据 window size 计算 self.cell_size, self.radius, self.board_rect
        # 保持棋盘正方形并居中
        w, h = self.screen.get_size()
        if w < MIN_WIDTH or h < MIN_HEIGHT:
            w, h = max(w, MIN_WIDTH), max(h, MIN_HEIGHT)
            self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        
        top_margin = 120
        bottom_margin = 100 if "REVIEW" in self.state else 60
        size = min(w - 40, h - top_margin - bottom_margin)
        self.cell_size = size // self.N
        self.radius = int(self.cell_size * 0.4)
        
        sx = (w - self.cell_size * self.N) // 2
        sy = top_margin + (h - top_margin - bottom_margin - self.cell_size * self.N) // 2
        self.board_rect = pygame.Rect(sx, sy, self.cell_size * self.N, self.cell_size * self.N)

    def draw_btn(self, rect, text, bg_color=COLOR_BTN, text_color=(255,255,255), enabled=True, is_popup=False):
        """绘制按钮并返回点击状态"""
        # TODO: 绘制圆角矩形和文字
        # 处理 hover 变色
        # 如果 (clicked and enabled and not popup_blocking): return True
        if not enabled: bg_color = COLOR_BTN_GRAY
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        
        if self.popup and not is_popup:
            col = bg_color
            clicked = False
        else:
            col = COLOR_BTN_HOVER if hover and enabled else bg_color
            clicked = hover and self.click_event and enabled

        pygame.draw.rect(self.screen, col, rect, border_radius=8)
        txt = self.font_mid.render(text, True, text_color)
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
        return clicked

    def draw_custom_input(self, rect, text, is_active=False):
        """绘制输入框 (带光标闪烁效果)"""
        # TODO: 绘制白底框 + 边框 (active时变色)
        # 绘制 text + 光标('|')
        # 使用 set_clip 防止文字溢出
        bc = COLOR_BTN if is_active else COLOR_TEXT
        thick = 3 if is_active else 2
        pygame.draw.rect(self.screen, (255, 255, 255), rect)
        pygame.draw.rect(self.screen, bc, rect, thick)
        
        display_txt = text + ("|" if is_active and (time.time() % 1 > 0.5) else "")
        txt_surf = self.font_mid.render(display_txt, True, COLOR_TEXT)
        
        self.screen.set_clip(rect.inflate(-10, -10))
        self.screen.blit(txt_surf, (rect.x + 5, rect.y + 5))
        self.screen.set_clip(None)

    def handle_input(self):
        """全局事件处理 (鼠标、键盘)"""
        self.click_event = False
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.network.close()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                self.resize_layout()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.click_event = True
            elif event.type == pygame.KEYDOWN:
                # TODO: 键盘输入路由
                # 如果有 popup -> 仅处理 Enter (关闭ALERT)
                # 如果在 NEW_GAME -> 处理 input_text/obs/time 的输入 (Tab切换焦点)
                # 如果在 NET_JOIN_INPUT -> 处理 IP 输入
                # 如果在 DIALOG_SAVE -> 处理文件名输入
                if self.popup:
                    if event.key == pygame.K_RETURN and self.popup['type'] == 'ALERT': self.popup = None
                    continue

                if self.state == "NEW_GAME":
                    if event.key == pygame.K_TAB:
                        order = ["TEXT", "OBS", "TIME"]
                        try: 
                            idx = order.index(self.active_input)
                            self.active_input = order[(idx+1)%3]
                        except: 
                            self.active_input = "TEXT"
                    elif event.key == pygame.K_RETURN:
                        if self.is_online and self.game_mode == "PvP": self.start_net_select()
                        else: self.attempt_start_game()
                    elif event.key == pygame.K_BACKSPACE:
                        if self.active_input == "TEXT": self.input_text = self.input_text[:-1]
                        elif self.active_input == "OBS": self.input_obs = self.input_obs[:-1]
                        else: self.input_time = self.input_time[:-1]
                    else:
                        c = event.unicode
                        if c.isdigit():
                            if self.active_input == "TEXT" and len(self.input_text) < 2: self.input_text += c
                            elif self.active_input == "OBS" and len(self.input_obs) < 3: self.input_obs += c
                            elif self.active_input == "TIME" and len(self.input_time) < 3: self.input_time += c

                elif self.state == "NET_JOIN_INPUT":
                    if event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_RETURN: self.attempt_join_game()
                    elif len(self.input_text) < 15 and (event.unicode.isdigit() or event.unicode in ".:"): self.input_text += event.unicode
                
                elif self.state in ["DIALOG_SAVE", "DIALOG_REVIEW_SAVE"]:
                    if event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_RETURN: self.trigger_dialog_confirm()
                    elif len(self.input_text) < 20 and (event.unicode.isalnum() or event.unicode in "_-"): self.input_text += event.unicode

    def trigger_dialog_confirm(self):
        """处理输入弹窗的确认 (保存/重命名等)"""
        # TODO: 根据当前 state 执行 save_game 或 save_review
        # 存盘后切回 MAIN
        if self.input_text:
            if self.state == "DIALOG_SAVE":
                data = {'match': self.match.to_dict(), 'turn': self.turn, 'time_left': self.time_left,
                        'game_mode': self.game_mode, 'difficulty_1': self.difficulty_1, 'use_timer': self.use_timer,
                        'time_limit_val': self.time_limit_val, 'is_online': self.is_online}
                storage.save_game(self.input_text, data)
                if self.is_online: self.network.close()
                self.is_online = False
                self.state = "MAIN"
            elif self.state == "DIALOG_REVIEW_SAVE":
                obs = [(r,c) for r in range(self.match.N) for c in range(self.match.N) if self.match.board[r][c]==3]
                data = {'N': self.match.N, 'obstacles': obs, 'moves': self.match.history, 'players': self.game_mode, 'winner': self.winner}
                storage.save_review(self.input_text, data)
                self.state = "MAIN"

    def attempt_start_game(self):
        """新游戏设置界面的 Start 校验"""
        # TODO: 校验 input_text(N), input_obs, input_time 是否合法
        # 如果合法 -> init_game(...)
        try:
            n = int(self.input_text)
            obs = int(self.input_obs)
            tm = int(self.input_time)
            if 4 <= n <= 20 and obs <= n*(n-1)//2 and tm >= 5:
                if self.is_online and self.game_mode == "PvP": self.start_net_select()
                else: self.init_game(n, self.game_mode, num_obstacles=obs, use_timer=self.use_timer, time_limit=tm)
                return
        except: pass
        self.show_popup("Invalid Settings!\nN: 4-20, Time>=5")

    # --- 网络连接辅助 ---
    def start_net_select(self): self.state = "NET_SELECT"
    def start_host_wait(self):
        ok, res = self.network.start_host()
        if ok: 
            self.net_ip = res
            self.state = "NET_HOST_WAIT"
            self.net_msg = "Waiting..."
        else: 
            self.show_popup(f"Host Error:\n{res}")
    def start_join_input(self): 
        self.state = "NET_JOIN_INPUT"
        self.input_text = "127.0.0.1"
    def attempt_join_game(self):
        # TODO: 校验 IP 格式 (正则)
        # start_client -> 切换 NET_JOIN_WAIT
        ip = self.input_text.split(":")[0].strip()
        if ip != "localhost" and not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip):
            self.show_popup("Invalid IP")
            return
        self.net_msg = f"Connecting to {ip}..."
        ok, res = self.network.start_client(ip)
        if ok: 
            self.state = "NET_JOIN_WAIT"
            self.net_msg = "Connected! Waiting info..."
            self.is_online = True
        else: 
            self.show_popup(f"Failed: {res}")

    # ================= 渲染分发 (Draw) =================

    def draw(self):
        self.screen.fill(COLOR_BG)
        
        # 根据 state 分发绘制任务
        if self.state == "MAIN": self.draw_main_menu()
        elif self.state == "NEW_GAME": self.draw_new_game()
        elif self.state == "NET_SELECT": self.draw_net_select()
        elif self.state == "NET_HOST_WAIT": self.draw_net_host()
        elif self.state == "NET_JOIN_INPUT": self.draw_net_join()
        elif self.state == "NET_JOIN_WAIT": self.draw_net_join_wait()
        
        elif self.state == "SAVES": self.draw_file_list("Select Save", True)
        elif self.state == "REVIEWS": self.draw_file_list("Select Replay", False)
        
        elif self.state.startswith("PLAYING") or self.state == "ANIMATING": 
            self.draw_game_interface()
        elif self.state == "GAMEOVER": 
            self.draw_gameover()
            
        elif self.state in ["DIALOG_SAVE", "DIALOG_REVIEW_SAVE"]: 
            self.draw_dialog("Enter Filename:")
        elif self.state == "DIALOG_EDIT_MODE": 
            self.draw_file_list("Select Save", True)
            self.draw_edit_mode_dialog()
            
        elif self.state == "REVIEW_PLAYING": 
            self.draw_review_interface()
            
        if self.popup: self.draw_popup_window()
        
        pygame.display.flip()

    # ================= 具体界面绘制方法 =================

    def draw_main_menu(self):
        """主菜单: New Game, Continue, Review, Quit"""
        # TODO: 绘制标题
        # TODO: 绘制按钮组，处理跳转
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        t = self.font_title.render("Gravity Connect 4", True, COLOR_TEXT)
        self.screen.blit(t, (cx - t.get_width()//2, 120))
        
        btns = [("New Game", "NEW_GAME", None), ("Continue", "SAVES", storage.list_saves),
                ("Review", "REVIEWS", storage.list_reviews), ("Quit", "QUIT", None)]
        y = 300
        for txt, st, cb in btns:
            if st == "QUIT":
                if self.draw_btn(pygame.Rect(cx-150, y, 300, 60), txt, COLOR_BTN_RED):
                    self.network.close()
                    pygame.quit()
                    sys.exit()
            else:
                if self.draw_btn(pygame.Rect(cx-150, y, 300, 60), txt):
                    self.state = st
                    if st == "NEW_GAME": 
                        self.reset_ui_state()
                        self.input_text="8"
                    if cb: 
                        self.reset_ui_state()
                        self.file_list = cb()
            y += 80

    def draw_new_game(self):
        """
        新游戏设置页 (最复杂的静态页面)
        包含: N输入, 障碍物输入, Timer开关/输入, 模式按钮, 联机/本地按钮, AI难度按钮
        """
        # TODO: 绘制各个 Label 和 InputBox (使用 draw_custom_input)
        # TODO: 处理焦点切换 (点击输入框切换 active_input)
        # TODO: 绘制 Toggle 按钮 (PvP/PvAI, Local/Online, Easy/Med/Hard)
        # TODO: Start Game 按钮 -> attempt_start_game
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        self.screen.blit(self.font_title.render("Setup Game", True, COLOR_TEXT), (cx-130, 80))
        
        y = 200
        # Row 1
        self.screen.blit(self.font_mid.render("Size:", True, COLOR_TEXT), (cx-200, y+5))
        r1 = pygame.Rect(cx-130, y, 80, 40)
        if self.click_event and r1.collidepoint(pygame.mouse.get_pos()): self.active_input = "TEXT"
        self.draw_custom_input(r1, self.input_text, self.active_input == "TEXT")
        
        self.screen.blit(self.font_mid.render("Obs:", True, COLOR_TEXT), (cx-30, y+5))
        r2 = pygame.Rect(cx+30, y, 80, 40)
        if self.click_event and r2.collidepoint(pygame.mouse.get_pos()): self.active_input = "OBS"
        self.draw_custom_input(r2, self.input_obs, self.active_input == "OBS")

        # Timer
        tr = pygame.Rect(cx+140, y+7, 26, 26)
        pygame.draw.rect(self.screen, COLOR_TEXT, tr, 2)
        if self.use_timer: pygame.draw.rect(self.screen, COLOR_BTN, tr.inflate(-8,-8))
        if self.click_event and tr.collidepoint(pygame.mouse.get_pos()): self.use_timer = not self.use_timer
        if self.use_timer:
            r3 = pygame.Rect(cx+180, y, 60, 40)
            if self.click_event and r3.collidepoint(pygame.mouse.get_pos()): self.active_input = "TIME"
            self.draw_custom_input(r3, self.input_time, self.active_input == "TIME")
        
        y += 80
        # Mode
        self.screen.blit(self.font_mid.render("Mode:", True, COLOR_TEXT), (cx-200, y+5))
        for i, m in enumerate(["PvP", "PvAI", "AIvAI"]):
            c = COLOR_BTN_GREEN if self.game_mode == m else COLOR_BTN_GRAY
            if self.draw_btn(pygame.Rect(cx-100+i*110, y, 100, 40), m, c): self.game_mode = m
        
        if self.game_mode == "PvP":
            y += 80
            if self.draw_btn(pygame.Rect(cx-110, y, 100, 40), "Local", COLOR_BTN_GREEN if not self.is_online else COLOR_BTN_GRAY): self.is_online = False
            if self.draw_btn(pygame.Rect(cx+10, y, 100, 40), "Online", COLOR_BTN_GREEN if self.is_online else COLOR_BTN_GRAY): self.is_online = True
        
        if "AI" in self.game_mode:
            y += 80
            lbl = "AI Diff:" if self.game_mode == "PvAI" else "AI 1:"
            self.screen.blit(self.font_mid.render(lbl, True, COLOR_TEXT), (cx-200, y+5))
            for i, d in enumerate(["Easy", "Medium", "Hard"]):
                c = COLOR_BTN if self.difficulty_1 != d else COLOR_BTN_HOVER
                if self.draw_btn(pygame.Rect(cx-100+i*110, y, 100, 40), d, c): self.difficulty_1 = d
            
            if self.game_mode == "AIvAI":
                y += 60
                self.screen.blit(self.font_mid.render("AI 2:", True, COLOR_TEXT), (cx-200, y+5))
                for i, d in enumerate(["Easy", "Medium", "Hard"]):
                    c = COLOR_BTN if self.difficulty_2 != d else COLOR_BTN_HOVER
                    if self.draw_btn(pygame.Rect(cx-100+i*110, y, 100, 40), d, c): self.difficulty_2 = d

        y = 650
        if self.draw_btn(pygame.Rect(cx-160, y, 140, 50), "Start", COLOR_BTN_GREEN): self.attempt_start_game()
        if self.draw_btn(pygame.Rect(cx+20, y, 140, 50), "Back", COLOR_BTN_GRAY): self.state = "MAIN"

    def draw_net_select(self):
        """选择 Host 还是 Client"""
        # TODO: 两个大按钮 Create / Join
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        self.screen.blit(self.font_title.render("Online PvP", True, COLOR_TEXT), (cx-120, 150))
        if self.draw_btn(pygame.Rect(cx-150, cy-60, 300, 60), "Create Host"): self.start_host_wait()
        if self.draw_btn(pygame.Rect(cx-150, cy+40, 300, 60), "Join Game"): self.start_join_input()
        if self.draw_btn(pygame.Rect(cx-150, cy+140, 300, 60), "Back", COLOR_BTN_GRAY): self.state = "NEW_GAME"

    def draw_net_host(self):
        """Host 等待界面: 显示本机 IP 和 Port"""
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        self.screen.blit(self.font_title.render("Waiting for Client...", True, COLOR_TEXT), (cx-200, 150))
        t1 = self.font_mid.render(f"IP: {self.net_ip}", True, COLOR_BTN)
        t2 = self.font_mid.render(f"Port: {network.DEFAULT_PORT}", True, COLOR_BTN)
        self.screen.blit(t1, (cx-t1.get_width()//2, cy-30))
        self.screen.blit(t2, (cx-t2.get_width()//2, cy+20))
        if self.draw_btn(pygame.Rect(cx-80, cy+100, 160, 50), "Cancel", COLOR_BTN_RED): 
            self.network.close()
            self.state = "NET_SELECT"

    def draw_net_join(self):
        """输入 Host IP 界面"""
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        self.screen.blit(self.font_title.render("Join Game", True, COLOR_TEXT), (cx-110, 150))
        self.screen.blit(self.font_mid.render("Host IP:", True, COLOR_TEXT), (cx-200, cy-50))
        self.draw_custom_input(pygame.Rect(cx-80, cy-55, 240, 50), self.input_text, True)
        if self.draw_btn(pygame.Rect(cx-80, cy+50, 160, 50), "Connect", COLOR_BTN_GREEN): 
            self.attempt_join_game()
        if self.draw_btn(pygame.Rect(cx-80, cy+120, 160, 50), "Back", COLOR_BTN_GRAY): 
            self.state = "NET_SELECT"

    def draw_net_join_wait(self):
        """连接中/等待 Host 开始"""
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        self.screen.blit(self.font_title.render("Connected!", True, COLOR_TEXT), (cx-120, 150))
        t = self.font_mid.render("Waiting for Host...", True, COLOR_BTN)
        self.screen.blit(t, (cx-t.get_width()//2, cy))
        if self.draw_btn(pygame.Rect(cx-80, cy+100, 160, 50), "Cancel", COLOR_BTN_RED): 
            self.network.close()
            self.state = "NET_SELECT"

    def draw_game_interface(self):
        """游戏主界面容器"""
        self.draw_board_area()
        # TODO: 绘制顶部状态栏 (Turn, Time, P1/P2)
        # TODO: 绘制 Exit, Save&Quit, Surrender 按钮
        w = self.screen.get_width()
        txt = f"Turn: P{self.turn}"
        if self.is_online: txt += f" (You: P{self.network.my_id})"
        if self.state == "PLAYING_AIvAI": txt = f"AI vs AI (P{self.turn})"
        if self.use_timer: txt += f" | Time: {int(self.time_left)}s"
        
        lbl = self.font_mid.render(txt, True, COLOR_TEXT)
        self.screen.blit(lbl, (w//2 - lbl.get_width()//2, 30))
        
        if self.draw_btn(pygame.Rect(20, 20, 80, 40), "Exit", COLOR_BTN_RED):
            self.show_popup("Quit without saving?", "CONFIRM", lambda: setattr(self, 'state', 'MAIN') or self.network.close())
        if self.draw_btn(pygame.Rect(110, 20, 120, 40), "Save&Quit"):
            self.state = "DIALOG_SAVE"
            self.input_text = f"save_{int(time.time())%1000}"
        if self.draw_btn(pygame.Rect(w-140, 20, 120, 40), "Surrender", COLOR_BTN_RED):
            if self.is_online: self.network.send({"type":"SURRENDER"})
            self.winner = 3 - self.turn
            self.state = "GAMEOVER"

    def draw_board_area(self):
        """
        绘制棋盘与棋子 (包含动画棋子)
        """
        if not self.board_rect: return
        
        # TODO 1: 绘制底板 (draw.rect)
        pygame.draw.rect(self.screen, COLOR_BOARD, self.board_rect, border_radius=15)
        
        # TODO 2: 鼠标悬停高亮 (仅当 PLAYING 且是我的回合)
        # 计算 col -> 绘制半透明列
        # if click -> attempt_move(col)
        can_click = (self.state == "PLAYING") and not self.popup
        if self.is_online and (self.turn != self.network.my_id): can_click = False
        if self.game_mode == "PvAI" and self.turn == 2: can_click = False
        
        if can_click and self.board_rect.collidepoint(pygame.mouse.get_pos()):
            c = (pygame.mouse.get_pos()[0] - self.board_rect.x) // self.cell_size
            hr = pygame.Rect(self.board_rect.x + c*self.cell_size, self.board_rect.y, self.cell_size, self.board_rect.height)
            s = pygame.Surface((self.cell_size, self.board_rect.height), pygame.SRCALPHA)
            s.fill(COLOR_HOVER)
            self.screen.blit(s, hr)
            if self.click_event: self.attempt_move(c)

        # TODO 3: 绘制静态棋子 (遍历 board)
        # 注意：障碍物(3)绘制成方块，棋子(1,2)绘制成圆
        for r in range(self.N):
            for c in range(self.N):
                cx = self.board_rect.x + c*self.cell_size + self.cell_size//2
                cy = self.board_rect.y + r*self.cell_size + self.cell_size//2
                v = self.match.board[r][c]
                col = COLOR_EMPTY
                if v == 1: col = COLOR_P1
                elif v == 2: col = COLOR_P2
                elif v == 3: col = COLOR_BLOCK
                
                if v == 3: pygame.draw.rect(self.screen, col, (cx-self.radius, cy-self.radius, self.radius*2, self.radius*2), border_radius=5)
                else: pygame.draw.circle(self.screen, col, (cx, cy), self.radius)

        # TODO 4: 绘制正在下落的动画棋子 (self.anim_piece)
        # 根据 anim_piece['x'] 和 ['y'] 绘制圆形
        if self.anim_piece:
            ap = self.anim_piece
            col = COLOR_P1 if ap['player'] == 1 else COLOR_P2
            pygame.draw.circle(self.screen, col, (ap['x'] + self.cell_size//2, int(ap['y']) + self.cell_size//2), self.radius)

    def draw_file_list(self, title, is_save):
        """通用文件列表 (存档/回放)"""
        # TODO: 绘制列表背景
        # TODO: 遍历 self.file_list 绘制每一项 (选中项高亮)
        # TODO: 底部按钮: Back, Load/Watch, Delete, Copy(仅存档), Edit Settings(仅存档)
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        self.screen.blit(self.font_title.render(title, True, COLOR_TEXT), (cx-120, 60))
        
        lr = pygame.Rect(cx-300, 130, 600, 450)
        pygame.draw.rect(self.screen, (255,255,255), lr)
        pygame.draw.rect(self.screen, COLOR_TEXT, lr, 2)
        
        sy = 140
        for i, item in enumerate(self.file_list):
            if sy > 570: break
            ir = pygame.Rect(cx-290, sy, 580, 40)
            if ir.collidepoint(pygame.mouse.get_pos()) and self.click_event and not self.popup: self.selected_file_idx = i
            c = COLOR_LIST_SEL if i == self.selected_file_idx else (255,255,255)
            pygame.draw.rect(self.screen, c, ir)
            
            info = item['filename'] + " | " + item.get('timestamp', '')
            if is_save: info += f" | {item['mode']}"
            t = self.font_small.render(info, True, COLOR_TEXT)
            self.screen.blit(t, (ir.x+10, ir.y+10))
            sy += 45
        
        by = 620
        if self.draw_btn(pygame.Rect(cx-350, by, 80, 50), "Back", COLOR_BTN_GRAY): self.state = "MAIN"
        if 0 <= self.selected_file_idx < len(self.file_list):
            fname = self.file_list[self.selected_file_idx]['filename']
            if self.draw_btn(pygame.Rect(cx-260, by, 80, 50), "Load" if is_save else "Watch", COLOR_BTN_GREEN):
                if is_save:
                    d = storage.load_game(fname)
                    if d.get('is_online'): 
                        self.pending_load_data = d
                        self.start_host_wait()
                    else: 
                        self.init_game(d['match']['N'], d.get('game_mode'), d)
                else: self.start_review(fname)
            
            if self.draw_btn(pygame.Rect(cx-170, by, 80, 50), "Delete", COLOR_BTN_RED):
                self.show_popup("Delete?", "CONFIRM", lambda: [storage.delete_save(fname) if is_save else storage.delete_review(fname), self.file_list.pop(self.selected_file_idx), setattr(self, 'selected_file_idx', -1)])
            
            if is_save:
                if self.draw_btn(pygame.Rect(cx-80, by, 80, 50), "Copy"): 
                    storage.copy_save(fname)
                    self.file_list = storage.list_saves()
                if self.draw_btn(pygame.Rect(cx+10, by, 120, 50), "Edit"): 
                    d = storage.load_game(fname)
                    self.edit_target_filename = fname
                    self.edit_temp_mode = d.get('game_mode', 'PvP')
                    self.edit_temp_online = d.get('is_online', False)
                    self.edit_temp_diff1 = d.get('difficulty_1', 'Medium')
                    self.edit_temp_diff2 = d.get('difficulty_2', 'Medium')
                    self.state = "DIALOG_EDIT_MODE"
    def draw_edit_mode_dialog(self):
        """在存档列表之上的弹窗，用于修改存档的模式/难度"""
        # TODO: 绘制遮罩和弹窗框
        # TODO: 绘制模式和难度选择按钮 (更新 temp 变量)
        # TODO: Save 按钮 -> storage.update_save_settings
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,150)); self.screen.blit(s, (0,0))
        
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        box = pygame.Rect(cx-250, cy-200, 500, 400) 
        pygame.draw.rect(self.screen, COLOR_BG, box, border_radius=10)
        
        self.screen.blit(self.font_mid.render("Edit Save Settings", True, COLOR_TEXT), (box.x+150, box.y+20))
        
        y = box.y + 70

        for i, m in enumerate(["PvP", "PvAI", "AIvAI"]):
            c = COLOR_BTN_GREEN if self.edit_temp_mode == m else COLOR_BTN_GRAY
            if self.draw_btn(pygame.Rect(box.x+80+i*120, y, 100, 40), m, c, is_popup=True): 
                self.edit_temp_mode = m
        
        y += 70

        if self.edit_temp_mode == "PvP":
            self.screen.blit(self.font_mid.render("Type:", True, COLOR_TEXT), (box.x+50, y+5))
            c_loc = COLOR_BTN_GREEN if not self.edit_temp_online else COLOR_BTN_GRAY
            c_net = COLOR_BTN_GREEN if self.edit_temp_online else COLOR_BTN_GRAY
            if self.draw_btn(pygame.Rect(box.x+150, y, 100, 40), "Local", c_loc, is_popup=True): self.edit_temp_online = False
            if self.draw_btn(pygame.Rect(box.x+270, y, 100, 40), "Online", c_net, is_popup=True): self.edit_temp_online = True
            
        elif "AI" in self.edit_temp_mode:
            lbl = "AI Diff:" if self.edit_temp_mode == "PvAI" else "AI 1:"
            self.screen.blit(self.font_mid.render(lbl, True, COLOR_TEXT), (box.x+50, y+5))
            for i, d in enumerate(["Easy", "Medium", "Hard"]):
                c = COLOR_BTN if self.edit_temp_diff1 != d else COLOR_BTN_HOVER
                if self.draw_btn(pygame.Rect(box.x+150+i*100, y, 90, 40), d, c, is_popup=True): self.edit_temp_diff1 = d
            
            if self.edit_temp_mode == "AIvAI":
                y += 60
                self.screen.blit(self.font_mid.render("AI 2:", True, COLOR_TEXT), (box.x+50, y+5))
                for i, d in enumerate(["Easy", "Medium", "Hard"]):
                    c = COLOR_BTN if self.edit_temp_diff2 != d else COLOR_BTN_HOVER
                    if self.draw_btn(pygame.Rect(box.x+150+i*100, y, 90, 40), d, c, is_popup=True): self.edit_temp_diff2 = d

        if self.draw_btn(pygame.Rect(box.x+100, box.bottom-60, 100, 40), "Save", COLOR_BTN_GREEN, is_popup=True):
            storage.update_save_settings(self.edit_target_filename, self.edit_temp_mode, 
                                       self.edit_temp_diff1, self.edit_temp_diff2, self.edit_temp_online)
            self.file_list = storage.list_saves(); self.state = "SAVES"
            
        if self.draw_btn(pygame.Rect(box.x+300, box.bottom-60, 100, 40), "Cancel", COLOR_BTN_RED, is_popup=True): 
            self.state = "SAVES"

    def draw_gameover(self):
        """游戏结算遮罩"""
        self.draw_board_area() # 保持背景
        # TODO: 绘制半透明黑底
        # TODO: 显示 Winner
        # TODO: Save Replay 按钮 -> 切换到 DIALOG_REVIEW_SAVE
        # TODO: Main Menu 按钮
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,180))
        self.screen.blit(s, (0,0))
        msg = f"Player {self.winner} Wins!" if self.winner else "Draw!"
        t = self.font_title.render(msg, True, (255,255,255))
        self.screen.blit(t, (self.screen.get_width()//2 - t.get_width()//2, 300))
        
        cx = self.screen.get_width()//2
        if self.draw_btn(pygame.Rect(cx-150, 400, 140, 50), "Save Replay"):
            self.state = "DIALOG_REVIEW_SAVE"
            self.input_text = f"rep_{int(time.time())%1000}"
        if self.draw_btn(pygame.Rect(cx+10, 400, 140, 50), "Main Menu", COLOR_BTN_GRAY): 
            self.state = "MAIN"

    def draw_dialog(self, prompt):
        """通用输入文件名弹窗"""
        # TODO: 绘制弹窗 + 输入框
        # OK / Cancel 按钮
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,150))
        self.screen.blit(s, (0,0))
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        box = pygame.Rect(cx-200, cy-100, 400, 200)
        pygame.draw.rect(self.screen, COLOR_BG, box, border_radius=10)
        
        self.screen.blit(self.font_mid.render(prompt, True, COLOR_TEXT), (box.x+20, box.y+20))
        self.draw_custom_input(pygame.Rect(box.x+20, box.y+60, 360, 40), self.input_text, True)
        
        if self.draw_btn(pygame.Rect(box.x+80, box.bottom-50, 100, 40), "OK", COLOR_BTN_GREEN): 
            self.trigger_dialog_confirm()
        if self.draw_btn(pygame.Rect(box.x+220, box.bottom-50, 100, 40), "Cancel", COLOR_BTN_RED): 
            self.state = "MAIN"

    def draw_popup_window(self):
        """通用 Alert/Confirm 弹窗"""
        # TODO: 绘制消息文本 (支持换行)
        # 如果是 CONFIRM: Yes/No 按钮
        # 如果是 ALERT: OK 按钮
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,150))
        self.screen.blit(s, (0,0))
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        box = pygame.Rect(cx-200, cy-100, 400, 200)
        pygame.draw.rect(self.screen, COLOR_BG, box, border_radius=10)
        pygame.draw.rect(self.screen, (200,50,50), box, 2, border_radius=10)
        
        lines = self.popup['msg'].split('\n')
        y = box.y + 40
        for l in lines:
            t = self.font_mid.render(l, True, COLOR_TEXT)
            self.screen.blit(t, (cx - t.get_width()//2, y))
            y += 30
        
        if self.popup['type'] == "CONFIRM":
            if self.draw_btn(pygame.Rect(cx-110, box.bottom-50, 100, 40), "Yes", COLOR_BTN_GREEN, is_popup=True):
                if self.popup['callback']: self.popup['callback']()
                self.popup = None
            if self.draw_btn(pygame.Rect(cx+10, box.bottom-50, 100, 40), "No", COLOR_BTN_RED, is_popup=True):
                if self.popup['no_callback']: self.popup['no_callback']()
                self.popup = None
        else:
            if self.draw_btn(pygame.Rect(cx-50, box.bottom-50, 100, 40), "OK", COLOR_BTN, is_popup=True): self.popup = None

    # --- 回放系统 ---
    def start_review(self, filename):
        """加载回放文件"""
        # TODO: load_review -> 初始化 match -> 切换到 REVIEW_PLAYING
        data = storage.load_review(filename)
        self.review_data = data
        self.review_moves = data['moves']
        self.review_step = 0
        self.N = data['N']
        self.match = Match(data['N'], obstacles=data.get('obstacles', []))
        self.resize_layout()
        self.state = "REVIEW_PLAYING"

    def draw_review_interface(self):
        """回放控制界面"""
        self.draw_board_area() # 复用棋盘绘制
        # TODO: 显示当前步数 Step X/Y
        # TODO: 按钮 << (重置), < (上一步), > (下一步), Exit
        # 逻辑：每次点击，重新 new Match 并模拟每一步 move
        t = self.font_mid.render(f"Step {self.review_step}/{len(self.review_moves)}", True, COLOR_TEXT)
        self.screen.blit(t, (self.screen.get_width()//2 - t.get_width()//2, 30))
        
        cx, y = self.screen.get_width()//2, self.screen.get_height()-80
        if self.draw_btn(pygame.Rect(cx-180, y, 50, 40), "<<"):
            self.review_step = 0
            self.match = Match(self.review_data['N'], obstacles=self.review_data.get('obstacles', []))
        
        if self.draw_btn(pygame.Rect(cx-120, y, 50, 40), "<") and self.review_step > 0:
            self.review_step -= 1
            self.match = Match(self.review_data['N'], obstacles=self.review_data.get('obstacles', []))
            for i in range(self.review_step): self.match.move(self.review_moves[i][1], self.review_moves[i][0])
            
        if self.draw_btn(pygame.Rect(cx-60, y, 50, 40), ">") and self.review_step < len(self.review_moves):
            m = self.review_moves[self.review_step]
            self.match.move(m[1], m[0])
            self.review_step += 1
            
        if self.draw_btn(pygame.Rect(cx+50, y, 80, 40), "Exit", COLOR_BTN_GRAY): self.state = "REVIEWS"

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    GameGUI().run()