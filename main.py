from ehrenfest_app.ui import EhrenfestApp
import customtkinter as ctk

def main():
    ctk.set_appearance_mode('light')
    ctk.set_default_color_theme('dark-blue')

    root = ctk.CTk()
    root.geometry('1200x700')
    app = EhrenfestApp(root)
    root.protocol('WM_DELETE_WINDOW', root.quit)
    root.mainloop()

if __name__ == '__main__':
    main()
