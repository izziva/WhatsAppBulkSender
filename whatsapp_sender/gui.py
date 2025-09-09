import customtkinter as ctk
import logging
import queue
import threading
import re
from tkinter import messagebox
from whatsapp_sender.data_manager import (
    read_message, read_numbers, save_message, save_numbers, 
    _load_numbers_from_db, clear_file, append_numbers_to_main_list
)
from whatsapp_sender.bot_wrapper import run_bot_instance
from whatsapp_sender.utils import get_failed_counts
from whatsapp_sender.config import settings

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.bot_thread = None
        self.stop_event = threading.Event()

        self.title("WhatsApp Sender")
        self.geometry("800x600")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Message frame
        self.message_frame = ctk.CTkFrame(self)
        self.message_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.message_frame.grid_columnconfigure(1, weight=1)
        self.message_label = ctk.CTkLabel(self.message_frame, text="Message:")
        self.message_label.grid(row=0, column=0, padx=10, pady=10)
        self.message_textbox = ctk.CTkTextbox(self.message_frame, height=100)
        self.message_textbox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.message_textbox.insert("1.0", read_message(gui_mode=True))

        # Numbers frame
        self.numbers_frame = ctk.CTkFrame(self)
        self.numbers_frame.grid(row=1, column=0, padx=10, pady=0, sticky="ew")
        self.numbers_frame.grid_columnconfigure(1, weight=1)

        self.numbers_label = ctk.CTkLabel(self.numbers_frame, text="Numbers:")
        self.numbers_label.grid(row=0, column=0, padx=10, pady=10)

        self.numbers_count_label = ctk.CTkLabel(self.numbers_frame, text="Count: 0")
        self.numbers_count_label.grid(row=1, column=0, padx=10, pady=0)

        self.failed_count_label = ctk.CTkLabel(self.numbers_frame, text="Failed: 0", cursor="hand2")
        self.failed_count_label.grid(row=2, column=0, padx=10, pady=0)
        self.failed_count_label.bind("<Button-1>", lambda e: self._show_failed_list())

        self.not_whatsapp_count_label = ctk.CTkLabel(self.numbers_frame, text="Not WA: 0", cursor="hand2")
        self.not_whatsapp_count_label.grid(row=3, column=0, padx=10, pady=0)
        self.not_whatsapp_count_label.bind("<Button-1>", lambda e: self._show_not_wa_list())

        self.numbers_textbox = ctk.CTkTextbox(self.numbers_frame, height=150)
        self.numbers_textbox.grid(row=0, column=1, rowspan=4, padx=10, pady=10, sticky="nsew")
        self.numbers_textbox.bind("<KeyRelease>", self._update_numbers_count)

        numbers = read_numbers(settings.NUMBERS_FILE, gui_mode=True)
        self.numbers_textbox.insert("1.0", ", ".join(numbers))

        # Log frame
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_textbox = ctk.CTkTextbox(self.log_frame, state="disabled", text_color="white")
        self.log_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Button frame
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.load_button = ctk.CTkButton(self.button_frame, text="Load Numbers from DB", command=self._load_numbers)
        self.load_button.grid(row=0, column=0, padx=10, pady=10)
        self.start_button = ctk.CTkButton(self.button_frame, text="Start Sending", command=self.start_bot)
        self.start_button.grid(row=0, column=1, padx=10, pady=10)
        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop", fg_color="red", command=self.stop_bot, state="disabled")
        self.stop_button.grid(row=0, column=2, padx=10, pady=10)

        # Setup logging
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        logging.basicConfig(level=logging.INFO, handlers=[self.queue_handler])
        self.logger = logging.getLogger()

        self.after(100, self.process_log_queue)
        self._update_numbers_count()
        self._update_failed_counts()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        if self.bot_thread and self.bot_thread.is_alive():
            if messagebox.askyesno("Exit", "Bot is still running. Do you want to stop it and exit?"):
                self.stop_bot()
                # Wait for the bot thread to finish before destroying the window
                self.after(100, self._wait_for_bot_and_destroy)
            else:
                return # Do not close
        else:
            self.destroy()

    def _wait_for_bot_and_destroy(self):
        if self.bot_thread and self.bot_thread.is_alive():
            self.after(100, self._wait_for_bot_and_destroy)
        else:
            self.destroy()

    def _show_numbers_popup(self, title, numbers, file_path):
        if not numbers:
            messagebox.showinfo(title, "The list is empty.")
            return

        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("350x450")
        popup.transient(self)

        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(0, weight=1)

        textbox = ctk.CTkTextbox(popup)
        textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        textbox.insert("1.0", ", ".join(numbers))
        textbox.configure(state="disabled")

        button_frame = ctk.CTkFrame(popup, fg_color="transparent")
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        def handle_clear():
            clear_file(file_path)
            self._update_failed_counts()
            popup.destroy()

        def handle_retry():
            append_numbers_to_main_list(numbers)
            clear_file(file_path)
            self._update_failed_counts()
            # Refresh main numbers textbox
            updated_main_numbers = read_numbers(settings.NUMBERS_FILE, gui_mode=True)
            self.numbers_textbox.delete("1.0", "end")
            self.numbers_textbox.insert("1.0", ", ".join(updated_main_numbers))
            self._update_numbers_count()
            popup.destroy()

        retry_button = ctk.CTkButton(button_frame, text="Retry All", command=handle_retry)
        retry_button.grid(row=0, column=0, padx=5, pady=5)

        clear_button = ctk.CTkButton(button_frame, text="Clear List", command=handle_clear)
        clear_button.grid(row=0, column=1, padx=5, pady=5)
        
        close_button = ctk.CTkButton(button_frame, text="Close", command=popup.destroy)
        close_button.grid(row=0, column=2, padx=5, pady=5)
        
        popup.wait_visibility()
        popup.grab_set()

    def _show_failed_list(self):
        file_path = settings.FAILED_NUMBERS_FILE
        failed_numbers = read_numbers(file_path, gui_mode=True)
        self._show_numbers_popup("Failed Numbers", failed_numbers, file_path)

    def _show_not_wa_list(self):
        file_path = settings.NOT_WAT_NUMBERS_FILE
        not_wa_numbers = read_numbers(file_path, gui_mode=True)
        self._show_numbers_popup("Not WhatsApp Numbers", not_wa_numbers, file_path)

    def _load_numbers(self):
        if not messagebox.askyesno(
            "Confirm Load",
            "Are you sure you want to load numbers from the database?\nThe current list will be overwritten."
        ):
            return

        try:
            numbers = _load_numbers_from_db()
            self.numbers_textbox.delete("1.0", "end")
            self.numbers_textbox.insert("1.0", ", ".join(numbers))
            self._update_numbers_count()
            self.logger.info(f"Successfully loaded {len(numbers)} numbers from the database.")
        except Exception as e:
            self.logger.error(f"Failed to load numbers from DB: {e}")

    def _update_numbers_count(self, event=None):
        numbers_str = self.numbers_textbox.get("1.0", "end-1c")
        numbers = [n.strip() for n in re.split(r',|\n', numbers_str) if n.strip()]
        self.numbers_count_label.configure(text=f"Count: {len(numbers)}")

    def _update_failed_counts(self):
        failed_count, not_whatsapp_count = get_failed_counts()
        self.failed_count_label.configure(text=f"Failed: {failed_count}")
        self.not_whatsapp_count_label.configure(text=f"Not WA: {not_whatsapp_count}")

    def process_log_queue(self):
        try:
            while True:
                record = self.log_queue.get_nowait()
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", record + "\n")
                self.log_textbox.configure(state="disabled")
                self.log_textbox.see("end")
        except queue.Empty:
            pass
        self.after(100, self.process_log_queue)
        self._update_failed_counts()

    def start_bot(self):
        message = self.message_textbox.get("1.0", "end-1c")
        if len(message) < 10:
            messagebox.showinfo("Warning", "Message must be at least 10 characters long.")
            return

        numbers_str = self.numbers_textbox.get("1.0", "end-1c")
        numbers: list[str] = [n.strip() for n in numbers_str.split(",") if n.strip()]

        save_message(message)
        save_numbers(settings.NUMBERS_FILE, numbers)

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.message_textbox.configure(state="disabled")
        self.numbers_textbox.configure(state="disabled")
        self.load_button.configure(state="disabled")
        self.stop_event.clear()

        self.bot_thread = threading.Thread(
            target=run_bot_instance,
            args=(self.logger, self.stop_event, lambda: self.after(0, self.update_gui_post_run))
        )
        self.bot_thread.start()

    def stop_bot(self):
        self.stop_event.set()
        self.logger.info("Stop signal sent. Waiting for bot to finish current task...")
        self.stop_button.configure(state="disabled")

    def update_gui_post_run(self):
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.message_textbox.configure(state="normal")
        self.numbers_textbox.configure(state="normal")
        self.load_button.configure(state="normal")

        # Reload numbers to show remaining ones
        remaining_numbers = read_numbers(settings.NUMBERS_FILE,gui_mode=True)
        self.numbers_textbox.delete("1.0", "end")
        self.numbers_textbox.insert("1.0", ", ".join(remaining_numbers))

if __name__ == '__main__':
    app = App()
    app.mainloop()
