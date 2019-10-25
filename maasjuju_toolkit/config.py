import os

base_dir = os.path.dirname(os.path.dirname(__file__))


class Config:
    # Base URL for MaaS API
    maas_api_url = os.getenv(
        'MJT_MAAS_API',
        'https://my.maas.server.ext:5240/MAAS/api/2.0'
    )

    # API Key
    maas_api_key = os.getenv(
        'MJT_MAAS_APIKEY',
        'AAAAAAAAA:BBBBBBBBBBB:CCCCCCCCCCCCC'
    )

    # SQLite database file
    sqlite_db = os.getenv(
        'MJT_SQLITE_DB',
        os.path.join(base_dir, 'cache.db')
    )
