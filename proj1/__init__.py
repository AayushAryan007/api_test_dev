import pymysql
from .celery import app as celery_app
# Patch version to satisfy Django 6.x requirement
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__ = "2.2.1"

pymysql.install_as_MySQLdb()

__all__ = ('celery_app',)