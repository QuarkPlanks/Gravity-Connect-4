import random
import math

# 常量定义，方便后续打分
EMPTY = 0
PLAYER_PIECE = 1  # 玩家棋子 (假设玩家是1)
AI_PIECE = 2      # AI棋子 (假设AI是2)
BLOCK = 3         # 障碍物

# 搜索窗口长度 (4个一连)
WINDOW_LENGTH = 4

class AIPlayer:
    def __init__(self, difficulty="Medium"):
        """
        :param difficulty: "Easy" (随机), "Medium" (浅层搜索), "Hard" (深层搜索)
        """
        self.difficulty = difficulty

    def get_best_move(self, match_obj, piece):
        """
        AI 的主入口函数。
        :param match_obj: 当前的 Match 对象 (包含棋盘 board, N 等)
        :param piece: AI 持有的棋子 (通常是 2)
        :return: 决定落子的列号 (col)
        """
        valid_locations = match_obj.get_valid_locations()
        
        # 没有任何空位，返回 None
        if not valid_locations:
            return None

        # TODO 1: Easy 难度
        # 直接从 valid_locations 中随机选一个返回
        if self.difficulty == "Easy":
            move = random.choice(valid_locations)
            return move

        # TODO 2: Medium / Hard 难度
        # 使用 Minimax 算法。
        # 如果是 Medium，深度 depth 设为 2。
        # 如果是 Hard，深度 depth 设为 4 (或者根据棋盘大小 N 动态调整，N越小深度可以越大)。
        elif self.difficulty == 'Medium':
            depth = 2
        elif self.difficulty == 'Hard':
            depth = 4
        # 调用 self.minimax(...) 获取最佳列和分数
        col, score = self.minimax(match_obj, depth, -10000, 100000, True, piece)
        # 注意：minimax 返回的是 (col, score)，这里只需要返回 col
        if col is None:
            col = random.choice(valid_locations)
            
        return col
        pass

    def evaluate_window(self, window, piece):
        """
        【估值核心】给一个长度为 4 的列表打分。
        例如 window = [2, 2, 0, 2] (AI是2)，这表示AI已经3连了，只要填个空就是4连。
        
        打分规则参考：
        - 4个全是 piece: +100分 (赢了)
        - 3个 piece + 1个空: +6分
        - 2个 piece + 2个空: +4分
        - 对手 3个 + 1个空: -4.5分 (危险！要防守)
        - 如果窗口里有障碍物(BLOCK)，得0分 (因为不可能连成线)
        """
        score = 0
        # 确定对手的棋子代码
        opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE
        ai_piece = AI_PIECE if piece == AI_PIECE else PLAYER_PIECE

        # TODO: 根据上述规则编写打分逻辑
        ai_piece_num = window.count(ai_piece) # 一个自己的棋 + 2分
        opp_piece_num = window.count(opp_piece) # 一个对手的棋 - 1.5分
        none_num = window.count(0) # 空不计分
        if BLOCK in window: # 有障碍记 0 分
            score = 0
            return score
        if ai_piece_num == 4:
            score = 100
        elif opp_piece_num == 4:
            score = -100
        else:
            score = 2*ai_piece_num - 1.5*opp_piece_num
        return score

    def score_position(self, match_obj, piece):
        """
        计算整个棋盘对于 piece 玩家的分数。
        """
        score = 0
        board = match_obj.board
        N = match_obj.N

        # TODO 1: 中心优先策略
        # 重力棋中，中间的列往往机会更多。
        # 获取中间一列 (column = N//2) 的所有棋子，统计 piece 的数量，乘以一个权重(比如3)，加到 score 里。
        center = [board[i][N // 2] for i in range(N)]
        score += self.evaluate_window(center, piece) * 2
        

        # TODO 2: 扫描所有可能的连线窗口 (横、竖、斜)
        # 类似于 Match.judge() 里的遍历，但这里不判断胜负，而是把切出来的 4个格子 传给 self.evaluate_window()
        # 将所有窗口的得分累加到 score。
        windows = []
        for each in board: # 行
            for pos in range(N - 3):
                windows.append([each[j] for j in range(pos, pos+4)])
        for each in range(len(board)): # 列
            line = [board[i][each] for i in range(len(board))]
            for pos in range(N - 3):
                windows.append([line[j] for j in range(pos, pos+4)])
        for i in range(N): # 对角线
            for j in range(N):
                if i + 3 <= N - 1 and j + 3 <= N - 1:
                        windows.append([board[i+k][j+k] for k in range(4)])
                if i+3 <= N - 1 and j-3 >= 0:
                        windows.append([board[i+k][j-k] for k in range(4)])
        for each in windows:
            score += self.evaluate_window(each, piece)
        return score

    def is_terminal_node(self, match_obj):
        """判断搜索是否应该终止：有人赢了，或者棋盘满了"""
        is_over, winner, _ = match_obj.judge()
        return is_over, winner

    def minimax(self, match_obj, depth, alpha, beta, maximizingPlayer, piece):
        """
        Minimax 算法实现 (带 Alpha-Beta 剪枝)。
        
        :param depth: 当前搜索深度
        :param alpha: 目前发现的最好的（最高的）最大值 (Maximizer 的底线)
        :param beta: 目前发现的最好的（最低的）最小值 (Minimizer 的底线)
        :param maximizingPlayer: True (AI回合), False (对手回合)
        :param piece: AI 的棋子 ID (例如 2)
        :return: (best_col, value) - 最佳列号和对应的分数
        """
        # 1. 获取有效落子位置
        valid_locations = match_obj.get_valid_locations()
        
        # 2. 检查终止条件 (深度为0 或 游戏结束)
        is_terminal, winner = self.is_terminal_node(match_obj)
        if depth == 0 or is_terminal:
            if is_terminal:
                if winner == piece:
                    return (None, 100000000000) # AI 赢 (给个极大值)
                elif winner != 0: 
                    return (None, -100000000000) # 对手赢 (给个极小值)
                else: 
                    return (None, 0) # 平局
            else:
                # 深度耗尽，返回当前盘面的静态估分
                return (None, self.score_position(match_obj, piece))

        # 3. Maximizing Branch (AI 回合 - 找最大分)
        if maximizingPlayer:
            value = -math.inf
            best_col = random.choice(valid_locations) # 默认随选一个防止空
            
            for col in valid_locations:
                # --- 模拟落子 ---
                # TODO 1: 创建副本
                temp_match = match_obj.copy()
                # TODO 2: 在副本上落子
                temp_match.move(col, piece)
                
                # --- 递归调用 ---
                # 注意：这里 maximizingPlayer 变成 False，传入 alpha 和 beta
                new_score = self.minimax(temp_match, depth-1, alpha, beta, False, piece)[1]
                
                # --- 更新最大值 ---
                # TODO 3: 
                if new_score > value:
                    value = new_score
                    best_col = col
                
                # --- Alpha-Beta 剪枝核心 ---
                # TODO 4: 更新 alpha
                alpha = max(alpha, value)
                
                # TODO 5: 剪枝判断
                if alpha >= beta:
                    break
                
            return best_col, value

        # 4. Minimizing Branch (对手回合 - 找最小分)
        else: 
            value = math.inf
            best_col = random.choice(valid_locations)
            
            # 计算对手的棋子ID (如果是1则2，是2则1)
            opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE
            
            for col in valid_locations:
                # --- 模拟落子 ---
                # TODO 1: 创建副本
                temp_match = match_obj.copy()
                # TODO 2: 在副本上落子 
                temp_match.move(col, opp_piece)
                
                # --- 递归调用 ---
                # 注意：这里 maximizingPlayer 变成 True
                new_score = self.minimax(temp_match, depth-1, alpha, beta, True, piece)[1]
                
                # --- 更新最小值 ---
                # TODO 3:
                if new_score < value:
                    value = new_score
                    best_col = col
                
                # --- Alpha-Beta 剪枝核心 ---
                # TODO 4: 更新 beta
                beta = min(beta, value)
                
                # TODO 5: 剪枝判断
                if beta <= alpha:
                    break
                
            return best_col, value