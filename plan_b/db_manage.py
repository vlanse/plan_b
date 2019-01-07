import os
import pathlib
from configparser import ConfigParser

from alembic.config import CommandLine, Config


def main():
    current_dir = os.path.abspath(os.getcwd())
    module_path = pathlib.Path(__file__).parent
    os.chdir(current_dir)

    cmd = CommandLine()
    cmd.parser.add_argument('--app-config', dest='db_config', required=True, help='service configuration file path')
    cmd_options = cmd.parser.parse_args()

    config = ConfigParser()
    config.read(cmd_options.db_config)
    db_url = config.get(section='db', option='url')
    if not db_url:
        cmd.parser.error(f'source config {cmd_options.db_config} contains empty "url" in [db] section')

    alembic_ini = Config(file_=str(module_path / 'alembic.ini'), ini_section=cmd_options.name, cmd_opts=cmd_options)
    alembic_ini.set_main_option('script_location', str(module_path / 'alembic'))
    alembic_ini.set_main_option('sqlalchemy.url', db_url)
    exit(cmd.run_cmd(alembic_ini, cmd_options))
