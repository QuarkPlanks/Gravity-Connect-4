import os
import json
import datetime
import shutil

# 定义存档文件夹路径
SAVES_DIR = "./saves"
REVIEWS_DIR = "./reviews"

def ensure_dirs():
    """TODO: 检查 SAVES_DIR 和 REVIEWS_DIR 是否存在，不存在则用 os.makedirs 创建"""
    if not os.path.exists(SAVES_DIR):
        os.makedirs(SAVES_DIR)
    if not os.path.exists(REVIEWS_DIR):
        os.makedirs(REVIEWS_DIR)

# --- 存档相关 ---

def save_game(filename, data):
    """
    保存游戏存档。
    :param filename: 用户输入的文件名
    :param data: 包含 'match', 'turn', 'time_left', 'game_mode' 等信息的字典
    """
    ensure_dirs()
    # TODO 1: 对 filename 进行清洗 (去掉非法字符)
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-')).rstrip()
    # TODO 2: 在 data 中加入 'timestamp' 字段，记录当前时间
    data['timestamp'] = datetime.datetime.now().isoformat()
    # TODO 3: 拼接完整路径 (SAVES_DIR + filename + .json)
    full_path = os.path.join(SAVES_DIR, filename + ".json")
    # TODO 4: 使用 open() 和 json.dump() 将 data 写入文件
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_game(filename):
    """TODO: 读取指定 json 文件并返回字典数据"""
    full_path = os.path.join(SAVES_DIR, filename + '.json')
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def list_saves():
    """
    列出所有存档及其元数据。
    :return: 一个列表，包含每个存档的 info 字典 (filename, mode, time, N 等)
    """
    ensure_dirs()
    saves = []
    # TODO 1: 使用 os.listdir 遍历 SAVES_DIR
    dir = os.listdir(SAVES_DIR)
    # TODO 2: 筛选 .json 结尾的文件
    save_files = []
    for each in dir:
        if each[-5:] == '.json':
            save_files.append(os.path.join(SAVES_DIR, each))
    # TODO 3: 依次读取文件，提取关键信息 (timestamp, mode, turn 等)，放入 saves 列表
    for save in save_files:
        with open(save, 'r', encoding='utf-8') as f:
            data = json.load(f)
            info = {
                'filename': os.path.basename(save).split('.')[0],
                'mode': data.get('game_mode', '未知模式'),
                'time': data.get('timestamp', '未知时间'),
                'N': data.get('match', {}).get('N', '未知大小'),
                'turn': data.get('turn', '未知回合')
            }
            saves.append(info)
        # print(saves)
    # TODO 4: 按 timestamp 倒序排列列表
    saves.sort(key=lambda x: x['time'], reverse=True)
    return saves

def delete_save(filename):
    """TODO: 删除指定存档文件"""
    full_path = os.path.join(SAVES_DIR, filename + '.json')
    if os.path.exists(full_path):
        os.remove(full_path)

def copy_save(filename):
    """
    复制存档功能。
    逻辑：读取源文件 -> 构造新文件名(加_copy_时间戳) -> 写入新文件
    """
    # TODO: 实现复制逻辑，利用 shutil.copy2
    ensure_dirs()
    savepath = os.path.join(SAVES_DIR, filename + ".json")
    name, ext = os.path.splitext(filename)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    new_filename = f"{name}_copy_{timestamp}{ext}"
    new_path = os.path.join(SAVES_DIR, new_filename + ".json")
    shutil.copy2(savepath, new_path)

def update_save_settings(filename, mode, diff1, diff2, is_online):
    """
    只更新存档的 设置部分 (用于在加载界面修改模式)。
    """
    # TODO: 读取 json -> 修改对应的字段 -> 重新写入 json
    savepath = os.path.join(SAVES_DIR, filename + ".json")
    with open(savepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data['game_mode'] = mode
        data['difficulty_1'] = diff1
        data['difficulty_2'] = diff2
        data['is_online'] = is_online
    with open(savepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 回放相关 (Review) ---
# 逻辑与存档类似，只是路径在 REVIEWS_DIR
# TODO: 实现 save_review, list_reviews, load_review, delete_review
# 结构与上面基本一致，仅文件夹不同
def save_review(filename, data):
    """
    保存游戏回放。
    :param filename: 用户输入的文件名
    :param data: 包含 'match', 'history' 等信息的字典
    """
    ensure_dirs()
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-')).rstrip()
    data['timestamp'] = datetime.datetime.now().isoformat()
    full_path = os.path.join(REVIEWS_DIR, filename + ".json")
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
def load_review(filename):
    """读取指定回放 json 文件并返回字典数据"""
    full_path = os.path.join(REVIEWS_DIR, filename + '.json')
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data
def list_reviews():
    """
    列出所有回放及其元数据。
    :return: 一个列表，包含每个回放的 info 字典 (filename, time, N 等)
    """
    ensure_dirs()
    reviews = []
    dir = os.listdir(REVIEWS_DIR)
    review_files = []
    for each in dir:
        if each[-5:] == '.json':
            review_files.append(os.path.join(REVIEWS_DIR, each))
    for review in review_files:
        with open(review, 'r', encoding='utf-8') as f:
            data = json.load(f)
            info = {
                'filename': os.path.basename(review).split('.')[0],
                'time': data.get('timestamp', '未知时间'),
                'N': data.get('match', {}).get('N', '未知大小'),
            }
            reviews.append(info)
    reviews.sort(key=lambda x: x['time'], reverse=True)
    return reviews
def delete_review(filename):
    """删除指定回放文件"""
    full_path = os.path.join(REVIEWS_DIR, filename + '.json')
    if os.path.exists(full_path):
        os.remove(full_path)