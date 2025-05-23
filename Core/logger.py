from typing import Optional
import logging
from enum import Enum
from abc import ABC, abstractmethod

from Core.config import settings

FILE_PATH = ""
"""Example Usage: C:/Project/AgentMate/Logs/"""

" -------------- ENUMS -------------- "
#region Enums
class FormatterType(Enum):
    SIMPLE = 0
    ADVANCED = 1


class LoggerType(Enum):
    CONSOLE = 0
    FILE = 1
#endregion

" -------------- FORMATTER -------------- "
#region Formatter
class IFormatter(ABC):
    @abstractmethod
    def get_formatter(self) -> logging.Formatter:
        pass


class SimpleFormatter(IFormatter):
    def get_formatter(self) -> logging.Formatter:
        return logging.Formatter('[%(asctime)s] => %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


class AdvancedFormatter(IFormatter):
    def get_formatter(self) -> logging.Formatter:
        return logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] => %(message)s %(details)s', datefmt='%Y-%m-%d %H:%M:%S')


class FormatterFactory:
    @staticmethod
    def create_formatter(formatter_type: FormatterType) -> IFormatter:
        formatter_map = {
            FormatterType.SIMPLE: SimpleFormatter,
            FormatterType.ADVANCED: AdvancedFormatter
        }
        formatter_class = formatter_map.get(formatter_type)
        if not formatter_class:
            raise ValueError("Invalid formatter type.")
        return formatter_class()
#endregion


" -------------- LOGGER -------------- "
#region Logger
class ILogger(ABC):
    @abstractmethod
    def log(self, level: int, message: str, extra: Optional[dict] = None):
        pass


class BaseLogger(ILogger):
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.propagate = False

    def log(self, level: int, message: str, extra: Optional[dict] = None):
        if settings.logging.enabled_levels[level]:
            self.logger.log(level, message, extra=extra)


class ConsoleLogger(BaseLogger):
    def __init__(self, name: str, formatter: IFormatter):
        super().__init__(name)

        if self.logger.handlers:
            return

        handler = logging.StreamHandler()
        handler.setFormatter(formatter.get_formatter())

        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)


class FileLogger(BaseLogger):
    def __init__(self, name: str, formatter: IFormatter, file_path: str):
        super().__init__(name)

        if self.logger.handlers:
            return

        handler = logging.FileHandler(file_path)
        handler.setFormatter(formatter.get_formatter())

        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)


class LoggerFactory:
    @staticmethod
    def create_logger(logger_type: LoggerType, name: str, formatter: FormatterType) -> ILogger:
        if logger_type == LoggerType.CONSOLE:
            return ConsoleLogger(name, formatter)
        elif logger_type == LoggerType.FILE:
            return FileLogger(name, formatter, f"{FILE_PATH}-{name}-Logger.txt")
        else:
            raise ValueError("Invalid logger type.")
#endregion

class Manager:
    def __init__(self, name: str, formatter_type: FormatterType, logger_type: LoggerType):
        formatter = FormatterFactory.create_formatter(formatter_type)
        self.logger = LoggerFactory.create_logger(logger_type, name, formatter)

    def debug(self, message: str, extra: Optional[dict] = None) -> None:
        self.logger.log(logging.DEBUG, message, extra=extra)

    def info(self, message: str, extra: Optional[dict] = None) -> None:
        self.logger.log(logging.INFO, message, extra=extra)

    def warning(self, message: str, extra: Optional[dict] = None) -> None:
        self.logger.log(logging.WARNING, message, extra=extra)

    def error(self, message: str, extra: Optional[dict] = None) -> None:
        self.logger.log(logging.ERROR, message, extra=extra)

    def fatal(self, message: str, extra: Optional[dict] = None) -> None:
        self.logger.log(logging.FATAL, message, extra=extra)

class LoggerCreator:
    @staticmethod
    def create_advanced_console(name: str) -> Manager:
        return Manager(name, formatter_type = FormatterType.ADVANCED, logger_type = LoggerType.CONSOLE)

    @staticmethod
    def create_simple_console(name: str) -> Manager:
        return Manager(name, formatter_type=FormatterType.SIMPLE, logger_type=LoggerType.CONSOLE)

    @staticmethod
    def create_advanced_file(name: str) -> Manager:
        return Manager(name, formatter_type=FormatterType.ADVANCED, logger_type=LoggerType.FILE)

    @staticmethod
    def create_simple_file(name: str) -> Manager:
        return Manager(name, formatter_type=FormatterType.SIMPLE, logger_type=LoggerType.FILE)

old_factory = logging.getLogRecordFactory()

def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    if not hasattr(record, "details"):
        record.details = ""
    return record

logging.setLogRecordFactory(record_factory)
