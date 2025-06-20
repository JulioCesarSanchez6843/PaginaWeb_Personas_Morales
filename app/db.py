#db.py
import cx_Oracle
import yaml

# Carga configuración desde YAML
with open('config/config.yml', 'r') as f:
    config = yaml.safe_load(f)

oracle_cfg = config['oracle']

dsn = cx_Oracle.makedsn(
    oracle_cfg['host'],
    oracle_cfg['port'],
    service_name=oracle_cfg['service_name']
)

def get_connection():
    return cx_Oracle.connect(
        user=oracle_cfg['user'],
        password=oracle_cfg['password'],
        dsn=dsn
    )

get_db = get_connection
