import io
import requests # for downloading cover art
import os
import shutil # for moving cover art to local directory
import threading # for running the download in a separate gui thread to avoid freezes
import customtkinter as ctk
from PIL import Image, ImageTk

from src.database import add_game, update_game, delete_game
from src.api import IGDBClient # for fetching game data from IGDB

# ---- Theme settings ----
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class GameForm(ctk.CTkFrame):
    def __init__(self, parent, game_data=None, on_back_callback=None):
        super().__init__(parent)
        self.parent = parent
        
        self.api_client = IGDBClient()  # initialize the IGDB client

         # keep track of selected game and search results
        self.search_results = []
        self.selected_game = None
        self.temp_image_data = None  # to hold the downloaded image data temporarily


        #layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # header row
        self.grid_rowconfigure(1, weight=1) # content row

        self.setup_ui(game_data, on_back_callback)
    
    def setup_ui(game_data, on_back_callback):
        self.on_back_callback = on_back_callback
        self.game_data = game_data
        self.is_edit_mode = game_data is not None

        self._create_top_navigation()
        self.create_content_containers()
        self._create_left_form_fields()
        self._create_right_sidebar()
    def _create_top_navigation(self):
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))

        # back button
        self.back_btn = ctk.CTkButton(self.top_frame, text="Back", command=self._on_back)
        self.back_btn.grid(side ="left")

        #header
        header_text = "Edit Game Details" if self.is_edit_mode else "Add New Game"
        self.header_lbl = ctk.CTkLabel(self.top_frame, text=header_text, font=ctk.CTkFont(size=18, weight="bold"))
        self.header_lbl.pack(side="left", padx=20)

    def _create_content_containers(self):
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=(5,20)) 
        
        # left side gets 3x horizontal stretching weight, right side gets 1x
        self.content_frame.grid_columnconfigure(0, weight=3)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        
    def _create_left_form_fields(self):
        # scrollable container on the left (column 0)
        self.form_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        self.form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.form_frame.grid_columnconfigure(0, weight=1)

        row_idx = 0

        # search bar section
        if not self.is_edit_mode:
            self.search_lbl = ctk.CTkLabel(self.form_frame, text="Search IGDB Database:", font=ctk.CTkFont(weight="bold"))
            self.search_lbl.grid(row=row_idx, column=0, sticky="w", pady=(10, 2))
            row_idx += 1

            self.search_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            self.search_frame.grid(row=row_idx, column=0, sticky="ew", pady=(0, 10))
            self.search_frame.grid_columnconfigure(0, weight=1)
            
            # entry for search string (binds enter key to run search)
            self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Type game title (e.g. Portal 2)...")
            self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
            self.search_entry.bind("<Return>", lambda event: self._on_search())
            
            self.search_btn = ctk.CTkButton(self.search_frame, text="Search", width=80, command=self._on_search)
            self.search_btn.grid(row=0, column=1)
            row_idx += 1

            # Option Menu dropdown to select matches
            self.matches_lbl = ctk.CTkLabel(self.form_frame, text="Select Matching Game:")
            self.matches_lbl.grid(row=row_idx, column=0, sticky="w", pady=(5, 2))
            row_idx += 1
            
            self.matches_combo = ctk.CTkOptionMenu(
                self.form_frame, 
                values=["Search a game to populate matches..."], 
                command=self._on_match_selected
            )
            self.matches_combo.grid(row=row_idx, column=0, sticky="ew", pady=(0, 15))
            row_idx += 1

        # title field
        self.title_lbl = ctk.CTkLabel(self.form_frame, text="Game Title:", font=ctk.CTkFont(weight="bold"))
        self.title_lbl.grid(row=row_idx, column=0, sticky="w", pady=(5, 2))
        row_idx += 1
        self.title_entry = ctk.CTkEntry(self.form_frame)
        self.title_entry.grid(row=row_idx, column=0, sticky="ew", pady=(0, 10))
        row_idx += 1

        # release date
        self.release_lbl = ctk.CTkLabel(self.form_frame, text="Release Date (YYYY-MM-DD):")
        self.release_lbl.grid(row=row_idx, column=0, sticky="w", pady=(5, 2))
        row_idx += 1
        self.release_entry = ctk.CTkEntry(self.form_frame, placeholder_text="YYYY-MM-DD")
        self.release_entry.grid(row=row_idx, column=0, sticky="ew", pady=(0, 10))
        row_idx += 1

        # developer
        self.dev_lbl = ctk.CTkLabel(self.form_frame, text="Developer(s):")
        self.dev_lbl.grid(row=row_idx, column=0, sticky="w", pady=(5, 2))
        row_idx += 1
        self.dev_entry = ctk.CTkEntry(self.form_frame)
        self.dev_entry.grid(row=row_idx, column=0, sticky="ew", pady=(0, 10))
        row_idx += 1

        # genre 
        self.genre_lbl = ctk.CTkLabel(self.form_frame, text="Genre(s):")
        self.genre_lbl.grid(row=row_idx, column=0, sticky="w", pady=(5, 2))
        row_idx += 1
        self.genre_entry = ctk.CTkEntry(self.form_frame)
        self.genre_entry.grid(row=row_idx, column=0, sticky="ew", pady=(0, 10))
        row_idx += 1

        # description textbox
        self.desc_lbl = ctk.CTkLabel(self.form_frame, text="Description:")
        self.desc_lbl.grid(row=row_idx, column=0, sticky="w", pady=(5, 2))
        row_idx += 1
        self.desc_textbox = ctk.CTkTextbox(self.form_frame, height=150)
        self.desc_textbox.grid(row=row_idx, column=0, sticky="ew", pady=(0, 15))

        # fill fields if were looking at an existing game
        if self.is_edit_mode:
            self._fill_form(self.game_data)

    def _fill_form(self, game_data):
        self.title_entry.insert(0, game_data.get("title", ""))
        self.release_entry.insert(0, game_data.get("release_date", ""))
        self.dev_entry.insert(0, game_data.get("developer", ""))
        self.genre_entry.insert(0, game_data.get("genre", ""))
        
        # clear textbox first, then insert description
        self.desc_textbox.delete("1.0", "end")
        self.desc_textbox.insert("1.0", game_data.get("description", ""))
    
    def _create_right_sidebar(self):
        # cover art preview, status dropdown, and action buttons on the right
        self.right_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # cover art preview label
        self.cover_lbl = ctk.CTkLabel(
            self.right_frame, 
            text="No Cover Art", 
            width=200, 
            height=280, 
            fg_color="#2b2b2b", 
            corner_radius=8
        )
        self.cover_lbl.pack(pady=(10, 15), fill="both", expand=True)

        # play status
        self.status_lbl = ctk.CTkLabel(self.right_frame, text="Library Status:", font=ctk.CTkFont(weight="bold"))
        self.status_lbl.pack(anchor="w")
        
        status_values = ["Backlog", "Playing", "Completed", "Abandoned"]
        initial_status = self.game_data.get("status", "Backlog") if self.is_edit_mode else "Backlog"
        self.status_combo = ctk.CTkOptionMenu(self.right_frame, values=status_values)
        self.status_combo.set(initial_status)
        self.status_combo.pack(fill="x", pady=(0, 20))

        # save
        save_btn_text = "Save Changes" if self.is_edit_mode else "Save Game"
        self.save_btn = ctk.CTkButton(
            self.right_frame, 
            text=save_btn_text, 
            fg_color="#1f6aa5", 
            hover_color="#144870", 
            command=self._on_save
        )
        self.save_btn.pack(fill="x", pady=(0, 10))

        # delete
        if self.is_edit_mode:
            self.delete_btn = ctk.CTkButton(
                self.right_frame, 
                text="Delete Game", 
                fg_color="#a83232", 
                hover_color="#7a2424", 
                command=self._on_delete
            )
            self.delete_btn.pack(fill="x")

        # load cover art if were in edit mode and a local path exists
        if self.is_edit_mode and self.game_data.get("local_cover_path"):
            self._load_local_cover(self.game_data["local_cover_path"])

    def _load_local_cover(self, image_path):
        """Loads a local cover image file and displays it in the preview area."""
        if not image_path or not os.path.exists(image_path):
            self.cover_lbl.configure(text="No Cover Art", image=None)
            return

        try:
            # Load image using pillow
            pil_img = Image.open(image_path)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 280))
            
            # configure label to show image and clear placeholder text
            self.cover_lbl.configure(image=ctk_img, text="")
            self.cover_lbl.image = ctk_img
        except Exception as e:
            print(f"Error loading local cover image: {e}")
            self.cover_lbl.configure(text="Error loading image", image=None)



    def _on_back(self):
        if self.on_back_callback:
            self.on_back_callback()

    def _on_search(self):
        # starts a background thread to search IGDB for the query entered in the search entry
        query = self.search_entry.get().strip() # get the search string from the entry field
        if not query:
            return # ignore empty searches

        # disable search fields to prevent spamming while fetching
        self.search_btn.configure(state="disabled", text="Searching...")
        self.search_entry.configure(state="disabled")
        
        # separate thread for background search to avoid freezing the GUI
        thread = threading.Thread(target=self._search_thread_target, args=(query,), daemon=True)
        thread.start()

    def _search_thread_target(self, query):
        # worker thread to call the IGDB API and fetch search results
        results = self.api_client.search_game(query)
        # Schedule the UI update safely back on the main thread
        self.after(0, self._on_search_complete, results)

    def _on_search_complete(self, results):
        # callback to populate the combobox dropdown with search matches
        # reenable search controls
        self.search_btn.configure(state="normal", text="Search")
        self.search_entry.configure(state="normal")

        self.search_results = results
        
        if not results:
            self.matches_combo.configure(values=["No matches found"])
            self.matches_combo.set("No matches found")
            return

        # create user-friendly dropdown options showing "Title (Year)"
        dropdown_options = []
        for game in results:
            year = game["release_date"][:4] if game["release_date"] != "Unknown" else "N/A"
            dropdown_options.append(f"{game['title']} ({year})")
        
        self.matches_combo.configure(values=dropdown_options)
        self.matches_combo.set("Select a match...")

    def _on_match_selected(self, choice):
        #fills form fields and downloads cover art when a dropdown choice is selected
        if choice in ["Search a game to populate matches...", "No matches found", "Select a match..."]:
            return

        # determine which game index was clicked
        try: 
            values = self.matches_combo.cget("values") # get the current list of dropdown values
            selected_idx = values.index(choice) # find the index of the selected choice in the dropdown values
            self.selected_game = self.search_results[selected_idx] # get the corresponding game metadata from the search results
        except (ValueError, IndexError):
            return

        # fill text inputs with said game metadata
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, self.selected_game["title"])

        self.release_entry.delete(0, "end")
        self.release_entry.insert(0, self.selected_game["release_date"])

        self.dev_entry.delete(0, "end")
        self.dev_entry.insert(0, self.selected_game["developer"])

        self.genre_entry.delete(0, "end")
        self.genre_entry.insert(0, self.selected_game["genre"])

        self.desc_textbox.delete("1.0", "end")
        self.desc_textbox.insert("1.0", self.selected_game["description"])

        # fetch and load the cover art preview asynchronously
        if self.selected_game["cover_url"]:
            self.cover_lbl.configure(text="Loading cover...")
            thread = threading.Thread(
                target=self._download_cover_thread_target, 
                args=(self.selected_game["cover_url"],), 
                daemon=True
            )
            thread.start()
        else:
            self.cover_lbl.configure(text="No Cover Art Available", image=None)
            self.temp_image_data = None

    def _download_cover_thread_target(self, url):
        # worker thread to download image binary bytes into memory
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            image_bytes = response.content
            # safely schedule the image renderer on the main thread
            self.after(0, self._on_cover_download_complete, image_bytes)
        except Exception as e:
            print(f"Failed to download cover art preview: {e}")
            self.after(0, lambda: self.cover_lbl.configure(text="Failed to load cover", image=None))

    def _on_cover_download_complete(self, image_bytes):
        # callback to convert binary bytes into a Pillow image and display it
        try:
            self.temp_image_data = image_bytes  # cache bytes in memory to save later
            
            # load from in memory stream using BytesIO
            pil_img = Image.open(io.BytesIO(image_bytes))
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 280))
            
            self.cover_lbl.configure(image=ctk_img, text="")
            self.cover_lbl.image = ctk_img
        except Exception as e:
            print(f"Error rendering cover preview: {e}")
            self.cover_lbl.configure(text="Error loading cover", image=None)

    def _on_save(self):
        #saves a new game or updates an existing game in the database
        title = self.title_entry.get().strip()
        release_date = self.release_entry.get().strip()
        developer = self.dev_entry.get().strip()
        genre = self.genre_entry.get().strip()
        description = self.desc_textbox.get("1.0", "end-1c").strip()
        status = self.status_combo.get()

        if not title:
            from tkinter import messagebox
            messagebox.showerror("Error", "Game Title is required!")
            return

        # handle saving the cover art file locally
        local_cover_path = None
        if self.temp_image_data:
            # get covers directory absolute path
            covers_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "covers"))
            os.makedirs(covers_dir, exist_ok=True)
            
            # create a clean file name based on title
            safe_title = "".join([c if c.isalnum() else "_" for c in title]).lower()  # isalnum ensures only letters and numbers are kept, others replaced with underscore
            local_cover_path_abs = os.path.join(covers_dir, f"{safe_title}.jpg") # absolute path to save the cover art
            
            try:
                with open(local_cover_path_abs, "wb") as f:
                    f.write(self.temp_image_data)
                #store relative path so database is portable, that way if the user moves the app folder, the relative path will still work
                local_cover_path = os.path.join("data", "covers", f"{safe_title}.jpg")
            except Exception as e:
                print(f"Failed to save cover art locally: {e}")
                local_cover_path = None
        elif self.is_edit_mode:
            # retain original cover path if we didnt fetch a new one
            local_cover_path = self.game_data.get("local_cover_path")

        from tkinter import messagebox
        if self.is_edit_mode:
            game_id = self.game_data["id"]
            success = update_game(game_id, title, release_date, developer, genre, description, status)
            if success:
                messagebox.showinfo("Success", f"'{title}' updated successfully!")
                self._on_back()
            else:
                messagebox.showerror("Error", f"Could not update game. A game with the title '{title}' might already exist.")
        else:
            cover_url = self.selected_game["cover_url"] if self.selected_game else None
            success = add_game(
                title=title,
                release_date=release_date,
                cover_url=cover_url,
                local_cover_path=local_cover_path,
                developer=developer,
                genre=genre,
                description=description,
                status=status
            )
            if success:
                messagebox.showinfo("Success", f"'{title}' saved successfully to your library!")
                self._on_back()
            else:
                messagebox.showerror("Error", f"A game named '{title}' is already in your library!")

    def _on_delete(self):
        # prompts confirmation and removes the game from library and deletes local cover file
        from tkinter import messagebox
        if not self.is_edit_mode:
            return
            
        title = self.game_data["title"]
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{title}' from your library?")
        if not confirm:
            return
            
        # delete local cover file if it exists
        local_path = self.game_data.get("local_cover_path")
        if local_path:
            # resolve relative path to abslute
            abs_local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", local_path))
            if os.path.exists(abs_local_path):
                try:
                    os.remove(abs_local_path) 
                except Exception as e: # if the file is missing or locked, we still want to delete the database record[]
                    print(f"Failed to delete local cover file: {e}")

        # delete database record 
        delete_game(self.game_data["id"])
        messagebox.showinfo("Deleted", f"'{title}' has been removed from your library.")
        self._on_back()