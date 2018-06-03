from flask_script import Manager

from app import create_app
from config import DevelopConfig
app=create_app(DevelopConfig)

manager=Manager(app)

from models import db
db.init_app(app)

from flask_migrate import Migrate,MigrateCommand
Migrate(app,db)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
