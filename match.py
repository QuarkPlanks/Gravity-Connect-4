import random
import copy

class Match:
    def __init__(self, N: int, board_data=None, obstacles=None, num_obstacles=3):
        """
        初始化对局。
        :param N: 棋盘大小 (N x N)
        :param board_data: (选填) 用于读档，现有的棋盘二维数组
        :param obstacles: (选填) 用于读档或回放，指定的障碍物坐标列表 [(r,c), ...]
        :param num_obstacles: (选填) 新游戏时需要随机生成的障碍物数量
        """
        self.N = N
        self.last_move = None  # 记录最后一步的位置 (row, col)，用于界面高亮
        self.history = []      # 记录每一步的落子 [(player, col), ...]，用于回放
        
        # TODO 1: 初始化 self.board
        # 如果传入了 board_data，直接使用它。
        # 否则，创建一个 N x N 的全 0 二维列表。
        if board_data is not None:
            self.board = board_data
        else:
            self.board = [[0 for i in range(N)] for j in range(N)]
        
        # TODO 2: 处理障碍物
        # 如果传入了 board_data，跳过此步。
        # 如果传入了 obstacles 列表，遍历列表将对应位置设为 3 (障碍物标记)。
        # 否则 (是新游戏)，调用 self._generate_obstacles(num_obstacles) 随机生成。
        if board_data is not None:
            pass
        else:
            if obstacles is not None:
                for each in obstacles:
                    self.board[each[0]][each[1]] = 3
            else:
                self._generate_obstacles(num_obstacles)

    def _generate_obstacles(self, count):
        """
        内部方法：随机生成障碍物。
        注意：
        1. 障碍物不能生成在第0行（入口），否则这一列就废了。
        2. 需要循环随机，直到成功放置了 count 个障碍物。
        3. 检查随机的位置是否已经是障碍物，避免重复。
        """
        # TODO: 实现随机生成逻辑
        obstacal_list = []
        for _ in range(count):
            i = random.randint(1, self.N - 1)
            j = random.randint(0, self.N - 1)
            obstacal_list.append((i, j))
        for each in obstacal_list:
            self.board[each[0]][each[1]] = 3

    def copy(self):
        """
        深拷贝当前对象，主要用于 AI 在“脑海”里模拟下棋，不影响真实棋盘。
        """
        # TODO: 创建一个新的 Match 对象，并将当前的 self.board 深拷贝给新对象
        board = copy.deepcopy(self.board)
        new_match = Match(self.N, board)
        return new_match
        

    def get_valid_locations(self):
        """
        AI 辅助方法：返回当前所有可以落子的列号列表。
        条件：该列的第 0 行 (top) 必须是空 (0)。
        """
        # TODO: 遍历所有列，收集可以下棋的列号
        column_list = []
        for i in range(self.N):
            if self.board[0][i] == 0:
                column_list.append(i)
        return column_list

    def get_target_row(self, col: int):
        """
        核心重力逻辑：计算如果在 col 列落子，棋子最终会落在第几行。
        
        :return: 目标行号。如果该列已满或不可落子，返回 -1。
        """
        # TODO 1: 边界检查 (col 是否在 0 到 N-1 之间)
        if not (col >= 0 and col <= self.N - 1):
            return -1
        # TODO 2: 检查第 0 行是否被堵住 (若是，返回 -1)
        if not self.board[0][col] == 0:
            return -1
        # TODO 3: 从第 1 行开始向下遍历，或者从第 N-1 行向上遍历。
        # 逻辑：找到从上往下数，第一个不是 0 的格子，它的上面一格就是落点。
        for i in range(self.N):
            if self.board[i][col] != 0:
                return i-1
            if i == self.N - 1:
                return i
    def move(self, col: int, player: int):
        """
        执行落子操作。
        """
        # TODO 1: 调用 self.get_target_row(col) 获取落点
        row = self.get_target_row(col)
        # TODO 2: 如果能落子 (row != -1):
        #         - 修改 self.board[row][col] = player
        #         - 更新 self.last_move
        #         - 将 (player, col) 追加到 self.history
        #         - 返回 True
        #         否则返回 False
        if row != -1:
            self.board[row][col] = player
            self.last_move = (row, col)
            self.history.append((player, col))
            return True
        else:
            return False

    def judge(self):
        """
        判断游戏胜负。
        :return: (is_over, winner, win_positions)
                 - is_over: bool, 游戏是否结束
                 - winner: int, 获胜者 (1, 2, 或 0表示平局)
                 - win_positions: list, 获胜棋子的坐标列表 (用于界面画线)，平局为 None
        """
        # 辅助内嵌函数：检查列表是否有连续4个相同的非0、非障碍物棋子
        def check_line(line):
            # TODO: 遍历列表，检查 line[i] == line[i+1] == ... == line[i+3]
            for i in range(len(line) - 3):
                if line[i] == line[i+1] == line[i+2] == line[i+3] and line[i] != 3 and line[i] != 0:
                    return (True, line[i], i)
            return (False, None, None)

        # TODO 1: 检查所有 横向 行
        for each in range(len(self.board)):
            is_over, winner, pos = check_line(self.board[each])
            if is_over:
                win_positions = [(each, j) for j in range(pos, pos+4)]
                return (is_over, winner, win_positions)
        # TODO 2: 检查所有 纵向 列
        for each in range(len(self.board)):
            line = [self.board[i][each] for i in range(len(self.board))]
            is_over, winner, pos = check_line(line)
            if is_over:
                win_positions = [(i, each) for i in range(pos, pos+4)]
                return (is_over, winner, win_positions)
        # TODO 3: 检查所有 对角线 (/) 和 反对角线 (\)
        # 提示：对角线检查可以用双重循环遍历棋盘上的每一个点，作为对角线的起点进行向后检测
        for i in range(self.N):
            for j in range(self.N):
                if i + 3 <= self.N - 1 and j + 3 <= self.N - 1:
                    if self.board[i][j] == self.board[i+1][j+1] == self.board[i+2][j+2] == self.board[i+3][j+3] and self.board[i][j] != 3 and self.board[i][j] != 0:
                        is_over = True
                        winner = self.board[i][j]
                        win_positions = [(i+k, j+k) for k in range(4)]
                        return (is_over, winner, win_positions)
                if i+3 <= self.N - 1 and j-3 >= 0:
                    if self.board[i][j] == self.board[i+1][j-1] == self.board[i+2][j-2] == self.board[i+3][j-3] and self.board[i][j] != 3 and self.board[i][j] != 0:
                        is_over = True
                        winner = self.board[i][j]
                        win_positions = [(i+k, j-k) for k in range(4)]
                        return (is_over, winner, win_positions)

        # TODO 4: 检查平局
        # 逻辑：如果所有列的第 0 行都不是 0 (入口全堵)，且前面没人赢，则平局。
        if 0 not in self.board[0]:
            return(True, 0, None)
        
        return (False, None, None)

    def to_dict(self):
        """序列化：将对象转为字典，用于 JSON 保存"""
        # TODO: 返回包含 N, board, history 的字典
        dictionary = {'N':self.N, 'board':self.board, 'history':self.history}
        return dictionary

    @staticmethod
    def from_dict(data):
        """反序列化：从字典创建对象"""
        # TODO: 读取 data 中的 N, board, history，创建一个新的 Match 对象并返回
        N = data['N']
        board = data['board']
        history = data.get('history', [])
        match = Match(N, board)
        match.history = history
        return match