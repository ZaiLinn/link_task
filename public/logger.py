import logging
from logging.handlers import TimedRotatingFileHandler

class LoggerConfig:
    def __init__(self, name, log_file, level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.log_file = log_file

        # 创建文件处理器
        file_handler = TimedRotatingFileHandler(
            self.log_file, when='H', interval=12, backupCount=14)
        file_handler.setLevel(logging.ERROR)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # 创建日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器到日志器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger