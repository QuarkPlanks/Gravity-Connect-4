# timer.py
import threading
import sys

class Timer:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.user_input = None
        self.timed_out = False

    def _get_input_thread(self):
        """
        内部方法：此方法将在子线程中运行，专门用于等待用户输入。
        """
        try:
            # TODO: 使用内置 input() 函数获取输入，赋值给 self.user_input
            # 注意：这里不需要打印提示语，提示语由主线程负责
            self.user_input = sys.stdin.readline().strip()
        except:
            pass

    def input_with_timeout(self, prompt):
        """
        带超时的输入函数。
        :param prompt: 输入提示语
        :return: 用户输入的字符串，如果超时则返回 None
        """
        print(prompt, end='', flush=True)
        
        # TODO 1: 创建一个 threading.Thread 对象
        input_thread = threading.Thread(target=self._get_input_thread)
        input_thread.daemon = True
        
        # TODO 2: 启动线程
        input_thread.start()
        input_thread.join(self.timeout)

        if input_thread.is_alive():
            # TODO 3: 如果 join 时间到了线程还在运行，说明超时了
            # 设置 self.timed_out 为 True
            # 打印一个换行符(冲掉提示语)，并返回 None
            self.timed_out = True
            print('\nTimed out')
            return None
        else:
            # 在规定时间内完成了输入
            return self.user_input