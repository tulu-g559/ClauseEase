import tkinter as tk
from tkinter import messagebox
USERNAME = "arnab"
PASSWORD = "1234"

def login():
    user = username_entry.get()
    pwd = password_entry.get()
    if user == USERNAME and pwd == PASSWORD:
        messagebox.showinfo("Login Success", f"Welcome, {user}!")
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")

# Create main window
root = tk.Tk()
root.title("Login Page")
root.geometry("300x200")
root.resizable(False, False)

# Username label and entry
tk.Label(root, text="Username").pack(pady=5)
username_entry = tk.Entry(root)
username_entry.pack(pady=5)

# Password label and entry
tk.Label(root, text="Password").pack(pady=5)
password_entry = tk.Entry(root, show="*")
password_entry.pack(pady=5)

# Login button
tk.Button(root, text="Login", command=login).pack(pady=20)

# Run the app
root.mainloop()
