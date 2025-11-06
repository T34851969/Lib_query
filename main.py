import tkinter as tk
from lib_query.gui import create_app


if __name__ == "__main__":
    root = tk.Tk()
    app = create_app(root, load_tabs=True, theme='clam')
    root.mainloop()