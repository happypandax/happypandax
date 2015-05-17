from .database import db
from .gui import app

conn = db.init_db()
DB = db.DBThread(conn)

WINDOW = app.AppWindow()
