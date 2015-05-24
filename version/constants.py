from .database import db
from .gui import app

#IMPORTANT STUFF
conn = db.init_db()
DB = db.DBThread(conn)
WINDOW = app.AppWindow()