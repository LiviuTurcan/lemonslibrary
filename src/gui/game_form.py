import io
import requests # for downloading cover art
import os
import shutil # for moving cover art to local directory
import threading # for running the download in a separate gui thread to avoid freezes
import customtkinter as ctk
from PIL import Image, ImageTk

from src.database import add_game
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



# PLACEHOLDER METHODS FOR BUTTONS
# FOR TESTING
    def _on_back(self):
        # placeholder for navigating back to the gallery
        print("Back button clicked!")
        if self.on_back_callback:
            self.on_back_callback()

    def _on_search(self):
        # placeholder for searching IGDB database
        print(f"Search triggered for: {self.search_entry.get()}")

    def _on_match_selected(self, choice):
        # dropdown placeholder
        print(f"Dropdown choice selected: {choice}")

    def _on_save(self):
        # placeholder for whatever
        print("Save button clicked!")

    def _on_delete(self):
        # aoi koi daidaiiroooo no hi itai kimi nooo yokooo
        print("Delete button clicked!")