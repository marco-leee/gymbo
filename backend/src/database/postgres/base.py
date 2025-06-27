from functools import wraps
from sqlalchemy.exc import SQLAlchemyError


def db_transaction(func):
    """Decorator to handle database transactions with automatic rollback on error"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            self.session.commit()
            # Only refresh if the result is a SQLAlchemy model instance
            if hasattr(result, "__table__") and result in self.session:
                self.session.refresh(result)
            return result
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    return wrapper
