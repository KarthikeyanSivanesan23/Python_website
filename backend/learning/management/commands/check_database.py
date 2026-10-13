"""Read-only connection diagnostics; never prints passwords or connection URLs."""
import json
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Report safe database configuration and verify a real query without changing data.'

    def add_arguments(self, parser):
        parser.add_argument('--configuration-only', action='store_true')
        parser.add_argument('--expected-data-dir')

    def handle(self, *args, **options):
        config = settings.DATABASES['default']
        result = {key.lower(): str(config.get(key, '')) for key in ['ENGINE', 'HOST', 'PORT', 'USER', 'NAME']}
        if options['configuration_only']:
            self.stdout.write(json.dumps(result))
            return
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result['query_ok'] = cursor.fetchone()[0] == 1
                if connection.vendor == 'postgresql':
                    cursor.execute("SELECT current_database(), current_user, host(inet_server_addr()), inet_server_port(), current_setting('data_directory'), pg_postmaster_start_time()::text, current_setting('logging_collector'), current_setting('log_destination')")
                    row = cursor.fetchone()
                    result.update(dict(zip(['database', 'database_user', 'server_host', 'server_port', 'data_directory', 'server_started_at', 'logging_collector', 'log_destination'], row)))
                    expected = options.get('expected_data_dir')
                    if expected and Path(row[4]).resolve() != Path(expected).resolve():
                        raise CommandError('The responding PostgreSQL server is not the expected data directory. No changes were made.')
                names = set(connection.introspection.table_names(cursor))
                result['schema_ready'] = all(name in names for name in ['learning_lesson', 'learning_draft', 'learning_progress', 'learning_attempt'])
                result['counts'] = {}
                for name in ['learning_lesson', 'learning_draft', 'learning_progress', 'learning_attempt']:
                    if name in names:
                        cursor.execute(f'SELECT COUNT(*) FROM {connection.ops.quote_name(name)}')
                        result['counts'][name] = cursor.fetchone()[0]
        except CommandError:
            raise
        except Exception as exc:
            # Do not print driver diagnostics that could include a connection string.
            raise CommandError(f'Database query failed ({type(exc).__name__}). Check the configured host, port, role, database, and credentials locally.') from None
        self.stdout.write(json.dumps(result))
