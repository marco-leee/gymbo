from abc import ABC, abstractmethod

class Repo(ABC):
  @abstractmethod
  def update_exercise(self) -> None:
    pass
  
  @abstractmethod
  def update_media(self) -> None:
    pass
  
class CassandraRepo(Repo):
  def __init__(self):
    print("cassandra repo")
    
  def update_exercise(self):
    return "hi"
  
  def update_media(self):
    return super().update_media()