"""
Athena SCIP - Supabase Database Client
Handles connection pooling and retry logic
"""
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Thread-safe Supabase client with retry logic"""
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, url: str, key: str, max_retries: int = 3):
        if self._client is None:
            self.url = url
            self.key = key
            self.max_retries = max_retries
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Supabase client with retry options"""
        try:
            self._client = create_client(self.url, self.key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError))
    )
    def query(self, table: str, operation: str, **kwargs) -> Any:
        """
        Execute a query with automatic retry on failure
        
        Args:
            table: Table name
            operation: 'select', 'insert', 'update', 'delete'
            **kwargs: Query parameters
        
        Returns:
            Query result
        """
        if not self._client:
            self._initialize_client()
        
        try:
            query = self._client.table(table)
            
            if operation == 'select':
                result = query.select(kwargs.get('columns', '*'))
                if kwargs.get('limit'):
                    result = result.limit(kwargs['limit'])
                if kwargs.get('offset'):
                    result = result.offset(kwargs['offset'])
                if kwargs.get('order_by'):
                    result = result.order(kwargs['order_by'], desc=kwargs.get('desc', True))
                if kwargs.get('filters'):
                    for key, value in kwargs['filters'].items():
                        result = result.eq(key, value)
                return result.execute()
            
            elif operation == 'insert':
                return query.insert(kwargs.get('data', [])).execute()
            
            elif operation == 'update':
                return query.update(kwargs.get('data', {})).eq(kwargs.get('eq_field', 'id'), kwargs.get('eq_value')).execute()
            
            elif operation == 'delete':
                if kwargs.get('filters'):
                    query = query
                    for key, value in kwargs['filters'].items():
                        query = query.eq(key, value)
                return query.delete().execute()
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def get_events(self, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """Get events with optional filtering"""
        result = self.query('events', 'select', limit=limit, filters=filters)
        return result.data if result.data else []

    def get_events_count(self) -> int:
        """Get total event count"""
        result = self._client.table('events').select('*', count='exact').limit(0).execute()
        return result.count or 0

    def get_recommendations(self, limit: int = 50) -> List[Dict]:
        """Get recommendations"""
        result = self._client.table('recommendations')\
            .select('*, events(*)') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        return result.data if result.data else []

# Singleton instance
_supabase_client: Optional[SupabaseClient] = None

def get_supabase_client(url: str, key: str) -> SupabaseClient:
    """Get singleton Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient(url, key)
    return _supabase_client
