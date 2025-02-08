from abc import ABC, abstractmethod
import logging

logging.basicConfig(level=logging.INFO)


class ExternalClient(ABC):
    def __init__(self, conn_str: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.conn_str = conn_str

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def health_check(self) -> None:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def close() -> None:
        pass


class CoreRepo(ABC):
    @abstractmethod
    def update_exercise(self, exercise: dict) -> None:
        pass

    @abstractmethod
    def update_media(self, media: dict) -> None:
        pass
