from config import DevelopConfig
from app import create_app
app = create_app(DevelopConfig)

from models import db

db.init_app(app)
from flask_script import Manager
manager = Manager(app)

from flask_migrate import Migrate, MigrateCommand
Migrate(app, db)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
