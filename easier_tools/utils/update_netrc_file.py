# -*- coding: utf-8 -*-
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox


def save_credentials(root, username, password) -> None:
    """
    Saves the provided username and password as credentials in the .netrc file. File is located on the user's home directory.

    Args:
        root: The root window or parent widget.
        username: The username to be saved.
        password: The password to be saved.

    Returns:
        None
    """
    # username = username_entry.get()
    # password = password_entry.get()
    access_endpoint = "urs.earthdata.nasa.gov"

    # Logic check to ensure a user has entered credentials before saving
    if not username or not password:
        messagebox.showerror("Error", "Both username and password must be entered")
        return

    netrc_file = Path.home() / ".netrc"
    if netrc_file.exists():
        with netrc_file.open("r") as file:
            lines = file.readlines()
            for i in range(len(lines)):
                if access_endpoint in lines[i] and username in lines[i + 1]:
                    messagebox.showwarning(
                        "Warning",
                        f"Credentials for {username} already exist for {access_endpoint} endpoint.\n\nUpdating password...",
                    )
                    # if credentials already exist, update the password
                    lines[i + 2] = f"password {password}\n"
                    with netrc_file.open("w") as file:
                        file.writelines(lines)
                        root.destroy()
                        return

    # if file does not exist, create it and add the credentials
    with netrc_file.open("a") as file:
        file.write(
            f"machine {access_endpoint}\nlogin {username}\npassword {password}\n\n"
        )

    messagebox.showinfo("Success", f"Credentials saved to {netrc_file}")
    root.destroy()


def open_web_link() -> None:
    """
    Opens a web link to the Earthdata Login page.

    This function uses the webbrowser module to open the web link
    to the Earthdata Login page (https://urs.earthdata.nasa.gov).

    Parameters:
    None

    Returns:
    None
    """
    webbrowser.open("https://urs.earthdata.nasa.gov")


def update_netrc_file() -> None:
    """
    Updates the .netrc file with NASA Earthdata Login credentials.

    This function creates a GUI window using Tkinter to prompt the user to enter their NASA Earthdata Login credentials.
    The entered username and password are then passed to the `save_credentials` function to save them to the .netrc file.

    Args:
        None

    Returns:
        None
    """
    # TK object
    root = tk.Tk()

    # Window settings and header title
    root.title("Updating .netrc file")
    root.geometry("500x300")

    # Description
    description_label = tk.Label(
        root,
        text="Please enter you NASA Earthdata Login credentials below to save them to your .netrc file.",
    )
    description_label.pack()

    # Username and password input fields
    username_label = tk.Label(root, text="Username")
    username_label.pack(pady=5)
    username_entry = tk.Entry(root)
    username_entry.pack(padx=10, pady=10)

    password_label = tk.Label(root, text="Password")
    password_label.pack(pady=5)
    password_entry = tk.Entry(root, show="*")
    password_entry.pack(padx=10, pady=10)

    # Using lambda function because the `command` parameter of `tk.Button` can't take functions with arguments directly.
    save_button = tk.Button(
        root,
        text="Save",
        command=lambda: save_credentials(
            root, username_entry.get(), password_entry.get()
        ),
    )
    save_button.pack(pady=10)

    # Create account button
    web_link_label = tk.Label(
        root, text="Don't have an account? Click below to create one"
    )
    web_link_label.pack(pady=10)
    web_link_button = tk.Button(root, text="Create Account", command=open_web_link)
    web_link_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    update_netrc_file()
