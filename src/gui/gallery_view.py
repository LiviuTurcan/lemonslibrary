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

        # track card widgets for repositioning
        self.card_widgets = []
        self.last_width = 0

        # layout configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.setup_ui()

        self.scroll_frame.bind("<Configure>", self._on_resize)  # bind resize event to the gallery frame

    def setup_ui(self):
        # create a scrollable frame for the gallery
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self._build_card_widgets() # build the card widgets for the games and the "Add Game" card

        self.rebuild_grid()  # initial grid layout
    
    def _create_game_card(self, game):
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=8, cursor="hand2")
        
        local_path = game.get("local_cover_path")
        abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", local_path)) if local_path else None
        
        # load cover art or placeholder
        if abs_path and os.path.exists(abs_path):
            try:
                pil_img = Image.open(abs_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(130, 180))
                cover_lbl = ctk.CTkLabel(card, image=ctk_img, text="")
                cover_lbl.image = ctk_img  # Reference to prevent garbage collection
            except Exception:
                cover_lbl = ctk.CTkLabel(card, text="[Broken Cover]", width=130, height=180, fg_color="#1f1f1f")
        else:
            cover_lbl = ctk.CTkLabel(card, text="No Cover Art", width=130, height=180, fg_color="#1f1f1f")
            
        cover_lbl.pack(padx=10, pady=(10, 5))

        # Game Title Label
        title_lbl = ctk.CTkLabel(card, text=game["title"], font=ctk.CTkFont(size=13, weight="bold"), wraplength=130)
        title_lbl.pack(padx=10, pady=(0, 10))
        
        click_callback = lambda event=None, g=game: self.on_game_click(g)
        card.bind("<Button-1>", click_callback)
        cover_lbl.bind("<Button-1>", click_callback)
        title_lbl.bind("<Button-1>", click_callback)

        return card

    def _create_add_game_card(self):
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#202020", border_width=2, border_color="#333333", corner_radius=8, cursor="hand2")
        
        # Big '+' sign label
        plus_lbl = ctk.CTkLabel(card, text="+", font=ctk.CTkFont(size=48), width=130, height=180)
        plus_lbl.pack(padx=10, pady=(10, 5))
        
        # "Add Game" text label
        title_lbl = ctk.CTkLabel(card, text="Add Game", font=ctk.CTkFont(size=13, weight="bold"))
        title_lbl.pack(padx=10, pady=(0, 10))

        # Bind click event
        click_callback = lambda event=None: self.on_add_game_click()
        card.bind("<Button-1>", click_callback)
        plus_lbl.bind("<Button-1>", click_callback)
        title_lbl.bind("<Button-1>", click_callback)

        return card

    def _build_card_widgets(self):
        # create and cache card widgets for all games, without placing them in the grid yet
        # destroy any existing widgets to prevent memory leaks on refresh
        for card in self.card_widgets:
            card.destroy()
        self.card_widgets = []

        games = get_all_games()
        
        # build cards for each game
        for game in games:
            card_frame = self._create_game_card(game)
            self.card_widgets.append(card_frame)

        # build the final "+" card
        add_card_frame = self._create_add_game_card()
        self.card_widgets.append(add_card_frame)

    def _on_resize(self, event):
        # rebuild the grid layout only if the width has changed significantly to avoid excessive redraws
        if event.widget == self.scroll_frame:
            if abs(event.width - self.last_width) > 20:
                self.last_width = event.width
                self.rebuild_grid()

    def rebuild_grid(self):
        # dynamically calculates columns and grids all cached card widgets
        if not self.card_widgets: # if no card widgets theres nothing to grid
            return

         # read the last measured width of the scroll frame
        available_width = self.last_width
        if available_width <= 1:
            available_width = 800  # default fallback

        # target card step is 180px which is the card width and padding
        card_step = 180
        num_columns = max(1, available_width // card_step) # takes max of 1 to avoid division by zero

        # reset old grid column weights
        for i in range(20):  # Reset columns up to index 20
            self.scroll_frame.grid_columnconfigure(i, weight=0, minsize=0)

        # apply weights to the new columns
        for col_idx in range(num_columns):
            self.scroll_frame.grid_columnconfigure(col_idx, weight=1, minsize=160)

        # position all cards from our cache
        row = 0
        col = 0
        for card_frame in self.card_widgets: 
            card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            col += 1
            if col >= num_columns:
                col = 0
                row += 1

    def _on_view_toggle(self, value):
        # placeholder for view mode toggle functionality
        print(f"View mode toggled to: {value}")