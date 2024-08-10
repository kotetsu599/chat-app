import customtkinter as ctk
import tkinter as tk
import websocket
import json
import threading
import ssl
import random
import time
class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")

        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", self.toggle_fullscreen)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.username_frame = ctk.CTkFrame(root, corner_radius=10, fg_color='gray20')
        self.username_frame.pack(pady=10, padx=50, fill='x')

        self.username_label = ctk.CTkLabel(self.username_frame, text="ユーザーネームを入力:", text_color="white")
        self.username_label.pack(side=ctk.LEFT, padx=5)

        self.username_entry = ctk.CTkEntry(self.username_frame, width=200, placeholder_text="Enter your username")
        self.username_entry.pack(side=ctk.LEFT, padx=5)
        self.username_entry.bind("<KeyRelease>", self.check_username)

        self.set_username_button = ctk.CTkButton(self.username_frame, text="決定！", command=self.set_username, state=ctk.DISABLED,
                                               text_color='black', fg_color='lightblue', hover_color='skyblue')
        self.set_username_button.pack(side=ctk.LEFT, padx=5)

        self.chat_frame = ctk.CTkFrame(root)
        self.chat_frame.pack(fill="both", expand=True, pady=10, padx=10)

        self.sidebar = tk.Listbox(self.chat_frame, bg='gray20', fg='white', width=20)
        self.sidebar.pack(side=ctk.LEFT, fill='y', padx=5, expand=False)

        self.chat_area = tk.Text(self.chat_frame, state='normal', wrap='word', bg='black', fg='white')
        self.chat_area.pack(side=ctk.LEFT, fill='both', expand=True)

        self.message_frame = ctk.CTkFrame(root, corner_radius=10, fg_color='gray20')
        self.message_frame.pack(pady=5, padx=10, fill='x')

        self.message_entry = ctk.CTkEntry(self.message_frame, width=400, placeholder_text="Enter your message")
        self.message_entry.pack(side=ctk.LEFT, padx=5, fill='x', expand=True)
        self.message_entry.bind("<Return>", self.send_message_event)

        self.send_button = ctk.CTkButton(self.message_frame, text="Send", command=self.send_message, 
                                        text_color='black', fg_color='lightgreen', hover_color='lime')
        self.send_button.pack(side=ctk.RIGHT, padx=5)

        self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.ssl_context.load_verify_locations("cert.pem")


    def start_ws(self):
        self.ws = websocket.WebSocketApp(
            f"wss://fdsafdsa/?key={random.randint(1, 11451419194545) * 833}",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open

        self.thread = threading.Thread(target=self.run_ws, args=(self.ssl_context,))
        self.thread.start()

    def run_ws(self, ssl_context):
        self.ws.run_forever(sslopt={"context": ssl_context})

    def check_username(self, event=None):
        username = self.username_entry.get().strip()
        if username and len(username) <= 19:
            self.set_username_button.configure(state=ctk.NORMAL)
        else:
            self.set_username_button.configure(state=ctk.DISABLED)

    def set_username(self):
        self.username = self.username_entry.get()
        self.username_frame.pack_forget()
        self.start_ws()

    def send_message(self):
        message = self.message_entry.get()
        if message and hasattr(self, 'username'):
            if message.strip() == "/clear":
                self.chat_area.configure(state='normal')
                self.chat_area.delete('1.0', tk.END)
                self.chat_area.configure(state='disabled')
                self.message_entry.delete(0, ctk.END)
            elif len(message) <= 500:
                data = {
                    "username": self.username,
                    "content": message,
                    "nonce": time.time() * 114514
                }
                self.ws.send(json.dumps(data))
                self.message_entry.delete(0, ctk.END)
            else:
                self.display_error("メッセージが長すぎます。")

    def send_message_event(self, event):
        self.send_message()
        
    def on_message(self, ws, message):
        try:
            message = json.loads(message) 
            if "joined" in message and message["joined"]:
                join_message = f"{message['name']} さんが入室しました。\n"
                self.sidebar.insert(tk.END, message["name"])
                self.display_notification(join_message)
            elif "joined" in message and not message["joined"]:
                leave_message = f"{message['name']} さんが退室しました。\n"
                for i in range(self.sidebar.size()):
                    if self.sidebar.get(i) == message["name"]:
                        self.sidebar.delete(i)
                        break
                self.display_notification(leave_message)
            
            if "username" in message and "content" in message:
                self.chat_area.configure(state='normal')
                self.chat_area.insert(tk.END, f"{message['username']}: ", "username")
                self.chat_area.insert(tk.END, f"{message['content']}\n", "message")
                self.chat_area.configure(state='disabled')
                self.chat_area.yview(tk.END)
        
        except json.JSONDecodeError as e:
            self.display_error(f"JSON Decode Error: {e}")
        except KeyError as e:
            self.display_error(f"Missing key in message: {e}")
        except Exception as e:
            self.display_error(f"Unknown error: {e}")

    def display_error(self, error_message):
        self.chat_area.configure(state='normal')
        self.chat_area.insert(tk.END, f"エラー発生: {error_message}\n")
        self.chat_area.configure(state='disabled')
        self.chat_area.yview(tk.END)

    def display_notification(self, notification_message):
        self.chat_area.configure(state='normal')
        self.chat_area.insert(tk.END, notification_message, "notification")
        self.chat_area.configure(state='disabled')
        self.chat_area.yview(tk.END)

    def on_error(self, ws, error):
        self.display_error(f"エラー発生: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.display_error("### closed ###")

    def on_open(self, ws):
        join_message = {
            "joined": True,
            "name": self.username
        }
        self.ws.send(json.dumps(join_message))
        print("### connected ###")

    def toggle_fullscreen(self, event=None):
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)



if __name__ == "__main__":
    root = ctk.CTk()
    app = ChatClient(root)

    app.chat_area.tag_configure("username", foreground="lime", font=("Arial", 10, "bold"))
    app.chat_area.tag_configure("message", foreground="white", font=("Arial", 10))
    app.chat_area.tag_configure("notification", foreground="yellow", font=("Arial", 10, "italic"))

    root.mainloop()
