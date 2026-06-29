from typing import Optional
from sqlalchemy.orm import Session
from supabase import Client
import logging

class BaseService:
    """
    Base service class that provides common utilities such as database session,
    Supabase client, and a class-specific logger.
    """
    def __init__(self, db: Optional[Session] = None, supabase_client: Optional[Client] = None):
        self.db = db
        self.supabase = supabase_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
