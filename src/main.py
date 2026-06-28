import customtkinter as ctk

# Import database and GUI components
from src.database import init_db
from src.gui.gallery_view import GalleryView
from src.gui.game_form import GameForm

# Set appearance theme
ctk.set_appearance_mode("dark")


class LemonsLibraryApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("lemonslibrary")
        self.geometry("1100x650")
        
        # Initialize the database schema
        init_db()

        # Configure window grid layout (Column 0: Sidebar, Column 1: Main Content)
        self.grid_columnconfigure(0, weight=0)  # Sidebar does not stretch
        self.grid_columnconfigure(1, weight=1)  # Content stretches to fill screen
        self.grid_rowconfigure(0, weight=1)

        # Track the active view currently showing
        self.current_view = None

        # Build UI Sections
        self._create_sidebar()
        self._create_content_pane()

        # Start with the Gallery View as the default screen
        self.show_gallery()

    def _create_sidebar(self):
        # Sidebar Frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1e293b")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False) # Keep width fixed at 200px
        
        # Configure rows in sidebar (Header, Navigation, Spacer, Profile/Settings)
        self.sidebar_frame.grid_rowconfigure(0, weight=0) # Header
        self.sidebar_frame.grid_rowconfigure(1, weight=0) # Games button
        self.sidebar_frame.grid_rowconfigure(2, weight=0) # Movies button
        self.sidebar_frame.grid_rowconfigure(3, weight=0) # Shows button
        self.sidebar_frame.grid_rowconfigure(4, weight=1) # Spacer push bottom
        self.sidebar_frame.grid_rowconfigure(5, weight=0) # Profile row
        
        # --- 1. Sidebar Header ---
        self.logo_lbl = ctk.CTkLabel(
            self.sidebar_frame, 
            text="lemonslibrary", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#60a5fa" # Light blue accent color
        )
        self.logo_lbl.grid(row=0, column=0, padx=20, pady=(25, 30), sticky="w")

        # --- 2. Menu Navigation Buttons ---
        self.games_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="games", 
            anchor="w", 
            fg_color="#1e3a8a", # Selected blue highlight
            hover_color="#1e3a8a",
            command=self.show_gallery
        )
        self.games_btn.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # Dummy buttons for future expansion (disabled for now)
        self.movies_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="movies", 
            anchor="w", 
            fg_color="transparent", 
            text_color="#94a3b8",
            state="disabled"
        )
        self.movies_btn.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.shows_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="shows", 
            anchor="w", 
            fg_color="transparent", 
            text_color="#94a3b8",
            state="disabled"
        )
        self.shows_btn.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        # --- 3. Profile & Settings Panel (Bottom) ---
        self.profile_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.profile_frame.grid(row=5, column=0, padx=10, pady=20, sticky="ew")
        self.profile_frame.grid_columnconfigure(0, weight=1)
        
        # Profile Button
        self.profile_btn = ctk.CTkButton(
            self.profile_frame, 
            text="profile", 
            anchor="w", 
            width=120, 
            fg_color="transparent",
            hover_color="#334155"
        )
        self.profile_btn.grid(row=0, column=0, sticky="w")
        
        # Settings Icon / Button (Using a star or simple character star symbol for mockup similarity)
        self.settings_btn = ctk.CTkButton(
            self.profile_frame, 
            text="⚙", # Gears/settings character
            width=30, 
            fg_color="transparent",
            hover_color="#334155"
        )
        self.settings_btn.grid(row=0, column=1, padx=(5, 0))

    def _create_content_pane(self):
        # creates the main content wrapper frame on the right side of the screen
        self.content_pane = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_pane.grid(row=0, column=1, sticky="nsew")
        
        # Configure layout to let child frame expand
        self.content_pane.grid_columnconfigure(0, weight=1)
        self.content_pane.grid_rowconfigure(0, weight=1)

    def show_view(self, view_class, *args, **kwargs):
        #destroys the current view and loads a new frame class into the content pane
        if self.current_view is not None:
            self.current_view.destroy()

        # Instantiate the new view frame inside the content pane
        self.current_view = view_class(self.content_pane, *args, **kwargs)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_gallery(self):
        # displays the main grid gallery view 
        self.show_view(
            GalleryView, 
            on_add_game_click=self.show_add_game_form, 
            on_game_click=self.show_game_detail
        )

    def show_add_game_form(self):
        # displays the blank game search & add form
        self.show_view(
            GameForm, 
            game_data=None, 
            on_back_callback=self.show_gallery
        )

    def show_game_detail(self, game_data):
        # displays the populated edit form for a selected game
        self.show_view(
            GameForm, 
            game_data=game_data, 
            on_back_callback=self.show_gallery
        )


if __name__ == "__main__":
    app = LemonsLibraryApp()
    app.mainloop()