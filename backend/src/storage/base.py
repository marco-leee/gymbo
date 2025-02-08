from abc import ABC, abstractmethod


class StorageProvider(ABC):
  @abstractmethod
  def download_object(self, object_name: str, destination: str) -> str:
    pass
  
  @abstractmethod
  def upload_object(self, path: str, key: str) -> None:
    pass