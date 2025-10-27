from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.log.logging_mixin import LoggingMixin
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import time

# Logger
logger = LoggingMixin().log

# Default DAG arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Database configurations
SOURCE_DB_CONFIG = {
    'host': '10.10.200.126',
    'port': 3306,
    'user': 'atikapp',
    'password': 'A12!wErrjU76!uNN',
    'database': 'bat_crm_uat'
}

DEST_DB_CONFIG = {
    # Write to host MySQL (outside Docker). On Docker Desktop (Windows/macOS)
    # use host.docker.internal to reach the host from containers.
    'host': 'host.docker.internal',
    'port': 3306,
    'user': 'root',
    'password': 'atikur911091',
    'database': 'bat_crm_local'
}


def transfer_audit_log():
    try:
        logger.info("Connecting to source database...")
        retries = 3
        while retries > 0:
            try:
                source_conn = mysql.connector.connect(**SOURCE_DB_CONFIG, connect_timeout=30)
                break
            except Error as e:
                retries -= 1
                logger.warning(f"Source DB connection failed ({retries} retries left): {e}")
                time.sleep(5)

        if not source_conn or not source_conn.is_connected():
            raise Exception("Failed to connect to source DB")

        source_cursor = source_conn.cursor(dictionary=True)

        logger.info("Connecting to destination database...")
        dest_conn = mysql.connector.connect(**DEST_DB_CONFIG, connect_timeout=30)
        dest_cursor = dest_conn.cursor()

        # ✅ Select all audit_log rows (you can add WHERE filters if needed)
        query = "SELECT * FROM audit_log"
        logger.info(f"Executing query: {query}")
        source_cursor.execute(query)
        rows = source_cursor.fetchall()

        if not rows:
            logger.info("No data found in source audit_log table.")
            return

        logger.info(f"Fetched {len(rows)} rows from source audit_log.")

        # ✅ Create table if not exists on destination
        create_table_query = """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INT(11) NOT NULL AUTO_INCREMENT,
                remote_ip VARCHAR(64) COLLATE utf8_unicode_ci DEFAULT NULL,
                module VARCHAR(50) COLLATE utf8_unicode_ci DEFAULT NULL,
                details LONGBLOB,
                user_type VARCHAR(20) COLLATE utf8_unicode_ci DEFAULT NULL,
                company_ids VARCHAR(255) COLLATE utf8_unicode_ci DEFAULT '0',
                created_by INT(11) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_by INT(11) DEFAULT NULL,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            ) ENGINE=INNODB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
            """

        dest_cursor.execute(create_table_query)
        dest_conn.commit()

        # ✅ Prepare insert query with upsert logic
        columns = rows[0].keys()
        placeholders = ', '.join(['%s'] * len(columns))
        columns_string = ', '.join(columns)
        update_clause = ', '.join([f"{col}=VALUES({col})" for col in columns if col != 'id'])

        insert_query = (
            f"INSERT INTO audit_log ({columns_string}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {update_clause}"
        )

        logger.info("Starting data transfer...")

        # ✅ Bulk insert for performance
        values = [tuple(row.values()) for row in rows]
        dest_cursor.executemany(insert_query, values)
        dest_conn.commit()

        logger.info(f"✅ Successfully transferred {len(rows)} rows to local audit_log table.")

    except Error as e:
        logger.error(f"MySQL Error: {e}")
        raise
    finally:
        for cursor in ['source_cursor', 'dest_cursor']:
            if cursor in locals() and locals()[cursor]:
                try:
                    locals()[cursor].close()
                except:
                    pass
        for conn in ['source_conn', 'dest_conn']:
            if conn in locals() and locals()[conn]:
                try:
                    locals()[conn].close()
                except:
                    pass


# ✅ DAG definition
with DAG(
    'audit_log_data_migration',
    default_args=default_args,
    description='Migrate audit_log table from remote MySQL to local MySQL',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 10, 26),
    catchup=False,
    tags=['mysql', 'migration', 'audit_log']
) as dag:

    migrate_audit_log_task = PythonOperator(
        task_id='transfer_audit_log_data',
        python_callable=transfer_audit_log,
    )

    migrate_audit_log_task
