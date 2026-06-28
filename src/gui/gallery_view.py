import os
import customtkinter as ctk
from PIL import Image
from src.database import get_all_games

class GalleryView(ctk.CTkFrame):
    def __init__(self,parent, on_add_game_click, on_game_click):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.on_add_game_click = on_add_game_click
        self.on_game_click = on_game_click

        # layout configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.setup_ui()

    def setup_ui(self):
        # create a scrollable frame for the gallery
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # congfigure the columns inside the scrollable frame
        for col_idx in range(4):
            self.scroll_frame.grid_columnconfigure(col_idx, weight=1,minsize=160)
        
        games = get_all_games()
        row = 0
        col = 0
        max_columns = 4 # number of columns in the gallery

        for game in games: # create a card for each game in the database
            self._create_game_card(game, row, col) # create the "Add Game" card
            col +=1 # increment column index
            if col >= max_columns: # if we reach the max columns
                col = 0 # reset column index
                row += 1 # increment row index
        
        self._create_add_game_card(row, col) # create the "Add Game" card at the end
    
    def _create_game_card(self, game, row, col):
        #create a clickable card for a game with its cover image and title
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#2e2e2e", corner_radius=8, cursor="hand2")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        local_path = game.get("local_cover_path")
        abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", local_path)) if local_path else None
        
        if abs_path and os.path.exists(abs_path):
            try:
                pil_img = Image.open(abs_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(130, 180))
                cover_lbl = ctk.CTkLabel(card, image=ctk_img, text="")
                cover_lbl.image = ctk_img # keep a reference to avoid garbage collection
            except Exception:
                cover_lbl = ctk.CTkLabel(card, text="[Broken Cover]", width=130, height=180, fg_color="#1f1f1f")
        else:
            # Corrected alignment: this else matches the 'if abs_path' check
            cover_lbl = ctk.CTkLabel(card, text="No Cover Art", width=130, height=180, fg_color="#1f1f1f")
            
        cover_lbl.pack(padx=10, pady=(10, 5))
        title_lbl = ctk.CTkLabel(card, text=game["title"], font=ctk.CTkFont(size=13, weight="bold"), wraplength=130)
        title_lbl.pack(padx=10, pady=(0, 10))
        
        # Bind the click event to open details
        click_callback = lambda event=None, g=game: self.on_game_click(g)
        card.bind("<Button-1>", click_callback)
        cover_lbl.bind("<Button-1>", click_callback)
        title_lbl.bind("<Button-1>", click_callback)


    def _create_add_game_card(self, row, col):
        # create a card with a big '+' sign and "Add Game" label that is clickable
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#202020", border_width=2, border_color="#333333", corner_radius=8, cursor="hand2")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Big '+' sign label
        plus_lbl = ctk.CTkLabel(card, text="+", font=ctk.CTkFont(size=48), width=130, height=180)
        plus_lbl.pack(padx=10, pady=(10, 5))
        
        # "Add Game" label
        title_lbl = ctk.CTkLabel(card, text="Add Game", font=ctk.CTkFont(size=13, weight="bold"))
        title_lbl.pack(padx=10, pady=(0, 10))
        # Bind click event
        click_callback = lambda event=None: self.on_add_game_click()
        card.bind("<Button-1>", click_callback)
        plus_lbl.bind("<Button-1>", click_callback)
        title_lbl.bind("<Button-1>", click_callback)