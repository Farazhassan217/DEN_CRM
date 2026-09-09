from supabase import create_client, Client
from .config import settings


def get_supabase_client() -> Client:
    """Get Supabase client with anon key (for regular operations)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_supabase_admin_client() -> Client:
    """Get Supabase client with service role key (for admin operations)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


# Singleton clients
supabase_client = None
supabase_admin_client = None


def init_supabase_clients():
    """Initialize Supabase clients"""
    global supabase_client, supabase_admin_client
    supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    supabase_admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return supabase_client, supabase_admin_client


def get_client() -> Client:
    """Get the initialized Supabase client"""
    global supabase_client
    if supabase_client is None:
        init_supabase_clients()
    return supabase_client


def get_admin_client() -> Client:
    """Get the initialized Supabase admin client"""
    global supabase_admin_client
    if supabase_admin_client is None:
        init_supabase_clients()
    return supabase_admin_client
