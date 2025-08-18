import customtkinter as ctk
import logging
import queue
import threading
from whatsapp_sender.data_manager import read_message, read_numbers, save_message, save_numbers
from whatsapp_sender.bot_wrapper import run_bot_instance

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
        self.numbers_textbox = ctk.CTkTextbox(self.numbers_frame, height=150)
        self.numbers_textbox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        numbers = read_numbers(gui_mode=True)
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
        self.button_frame.grid_columnconfigure((0, 1), weight=1)
        self.start_button = ctk.CTkButton(self.button_frame, text="Start Sending", command=self.start_bot)
        self.start_button.grid(row=0, column=0, padx=10, pady=10)
        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop", fg_color="red", command=self.stop_bot, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=10, pady=10)

        # Setup logging
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        logging.basicConfig(level=logging.INFO, handlers=[self.queue_handler])
        self.logger = logging.getLogger()

        self.after(100, self.process_log_queue)

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

    def start_bot(self):
        message = self.message_textbox.get("1.0", "end-1c")
        numbers_str = self.numbers_textbox.get("1.0", "end-1c")
        numbers = [n.strip() for n in numbers_str.split(",") if n.strip()]

        save_message(message)
        save_numbers(numbers)

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.message_textbox.configure(state="disabled")
        self.numbers_textbox.configure(state="disabled")
        self.stop_event.clear()

        self.bot_thread = threading.Thread(
            target=run_bot_instance,
            args=(self.logger, self.stop_event, self.update_gui_post_run)
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

        # Reload numbers to show remaining ones
        remaining_numbers = read_numbers(gui_mode=True)
        self.numbers_textbox.delete("1.0", "end")
        self.numbers_textbox.insert("1.0", ", ".join(remaining_numbers))

if __name__ == '__main__':
    app = App()
    app.mainloop()
