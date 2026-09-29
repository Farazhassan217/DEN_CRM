from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from .config import settings

# Compatibility: supabase_sync expects a 'storage' attribute on ClientOptions
ClientOptions.storage = None  # type: ignore
# Compatibility: supabase_sync also expects an 'httpx_client' attribute
ClientOptions.httpx_client = None  # type: ignore


def get_supabase_client() -> Client:
    """Get Supabase client with anon key (for regular operations) with extended timeout"""
    options = ClientOptions(postgrest_client_timeout=60)  # 60 seconds timeout
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY, options=options)


def get_supabase_admin_client() -> Client:
    """Get Supabase client with service role key (for admin operations) with extended timeout"""
    options = ClientOptions(postgrest_client_timeout=60)  # 60 seconds timeout
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY, options=options)


# Singleton clients
supabase_client = None
supabase_admin_client = None


def init_supabase_clients():
    """Initialize Supabase clients with extended timeout"""
    global supabase_client, supabase_admin_client
    options = ClientOptions(postgrest_client_timeout=60)
    supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY, options=options)
    supabase_admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY, options=options)
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