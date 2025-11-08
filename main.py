"""主程序"""
import tkinter as tk
from lib_query.gui import create_app
from lib_query.ctrl import CentreCtrl
from lib_query.db.core import LibraryDatabase

if __name__ == "__main__":

    
    db = LibraryDatabase()
    ctrl = CentreCtrl(db)
    
    root = tk.Tk()
    app = create_app(root, ctrl=ctrl, load_tabs=True, theme='clam')

    root.mainloop()