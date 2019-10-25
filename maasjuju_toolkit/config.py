# Copyright (C) 2019  GRNET S.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
