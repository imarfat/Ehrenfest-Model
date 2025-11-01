from ehrenfest_app.ui import EhrenfestApp
import tkinter as tk

def main():
    root = tk.Tk()
    app = EhrenfestApp(root)
    root.protocol('WM_DELETE_WINDOW', root.quit)
    root.mainloop()

if __name__ == '__main__':
    main()
