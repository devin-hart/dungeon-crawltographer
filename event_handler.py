import pygame
import math

import config
from data_models import IconType

# Import tkinter for file dialogs
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

class EventHandler:
    def __init__(self, app):
        self.app = app

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.app.window_width = event.w
                self.app.window_height = event.h
                self.app.screen = pygame.display.set_mode((self.app.window_width, self.app.window_height), pygame.RESIZABLE)
            
            # Prioritize dialogs and text input over other events
            if self.app.is_dialog_open():
                if event.type == pygame.KEYDOWN:
                    self.handle_dialog_input(event)
                continue
            
            if self.app.input_mode:
                if event.type == pygame.KEYDOWN:
                    self.handle_label_input(event)
                continue

            # Handle other events if no dialogs are open
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_down(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.handle_mouse_up(event)
            elif event.type == pygame.MOUSEWHEEL:
                self.handle_mouse_wheel(event)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event)
            elif event.type == pygame.KEYDOWN:
                self.handle_key_down(event)

    def handle_mouse_down(self, event):
        mods = pygame.key.get_mods()
        if event.button == 1: # Left click
            if self.handle_ui_click(event.pos):
                return
            
            # Handle multi-selection
            if mods & pygame.KMOD_SHIFT:
                self.app.multi_select_mode = True
                self.app.selection_start_pos = self.app.screen_to_grid(*event.pos)
            else:
                self.app.left_mouse_down = True
                self.app.handle_click(event.pos, button=1)

        elif event.button == 3: # Right click
            if not (mods & pygame.KMOD_SHIFT): # Don't erase if starting a selection
                self.app.selected_cells.clear()
            self.app.right_mouse_down = True
            self.app.handle_click(event.pos, button=3)
        elif event.button == 2: # Middle click
            self.app.dragging = True
            self.app.drag_start_pos = event.pos
            self.app.drag_start_camera = (self.app.camera_x, self.app.camera_y)

    def handle_mouse_up(self, event):
        if event.button == 1:
            if self.app.multi_select_mode:
                self.app.multi_select_mode = False
                end_pos = self.app.screen_to_grid(*event.pos)
                if self.app.selection_start_pos and end_pos:
                    x_start, y_start = self.app.selection_start_pos
                    x_end, y_end = end_pos
                    
                    # Clear previous selection unless CTRL/CMD is held
                    mods = pygame.key.get_mods()
                    if not (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                        self.app.selected_cells.clear()

                    for x in range(min(x_start, x_end), max(x_start, x_end) + 1):
                        for y in range(min(y_start, y_end), max(y_start, y_end) + 1):
                            self.app.selected_cells.add((x, y))
                self.app.selection_start_pos = None

            self.app.left_mouse_down = False
            self.app.last_marked_cell = None
            self.app.save_state()
        elif event.button == 3:
            self.app.right_mouse_down = False
            self.app.last_marked_cell = None
            self.app.save_state()
        elif event.button == 2:
            self.app.dragging = False

    def handle_mouse_wheel(self, event):
        if event.y > 0: self.app.zoom = min(3.0, self.app.zoom * 1.1)
        elif event.y < 0: self.app.zoom = max(0.3, self.app.zoom / 1.1)

    def handle_mouse_motion(self, event):
        if self.app.left_mouse_down and not self.app.multi_select_mode and event.pos[1] > config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT + (config.ICON_PANEL_HEIGHT if self.app.show_icon_panel else 0):
            grid_pos = self.app.screen_to_grid(*event.pos)
            if grid_pos and grid_pos != self.app.last_marked_cell:
                # Directly call handle_click for drag-drawing to process one cell at a time
                self.app.handle_click(event.pos, button=1, is_drag=True)
                self.app.last_marked_cell = grid_pos
        elif self.app.right_mouse_down and not self.app.multi_select_mode and event.pos[1] > config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT + (config.ICON_PANEL_HEIGHT if self.app.show_icon_panel else 0):
            grid_pos = self.app.screen_to_grid(*event.pos)
            if grid_pos and grid_pos != self.app.last_marked_cell:
                self.app.handle_click(event.pos, button=3)
                self.app.last_marked_cell = grid_pos
        elif self.app.dragging:
            dx = (event.pos[0] - self.app.drag_start_pos[0]) / (config.CELL_SIZE * self.app.zoom)
            dy = (event.pos[1] - self.app.drag_start_pos[1]) / (config.CELL_SIZE * self.app.zoom)
            angle = math.radians(self.app.rotation)
            rotated_dx = dx * math.cos(angle) + dy * math.sin(angle)
            rotated_dy = -dx * math.sin(angle) + dy * math.cos(angle)
            self.app.camera_x = self.app.drag_start_camera[0] - rotated_dx
            self.app.camera_y = self.app.drag_start_camera[1] - rotated_dy

    def handle_key_down(self, event):
        mods = pygame.key.get_mods()
        # Undo/Redo
        if mods & pygame.KMOD_CTRL:
            if event.key == pygame.K_z: self.app.undo()
            elif event.key == pygame.K_y: self.app.redo()
            elif event.key == pygame.K_s: self.app.trigger_save()
            elif event.key == pygame.K_l: self.app.trigger_load()
            return

        # Movement and Camera
        if event.key == pygame.K_w: self.app.move_player()
        elif event.key == pygame.K_s: self.app.move_player(forward=False)
        elif event.key == pygame.K_a: self.app.rotation = (self.app.rotation + 90) % 360
        elif event.key == pygame.K_d: self.app.rotation = (self.app.rotation - 90) % 360
        elif event.key == pygame.K_UP: self.app.pan_camera(0, -1)
        elif event.key == pygame.K_DOWN: self.app.pan_camera(0, 1)
        elif event.key == pygame.K_LEFT: self.app.pan_camera(-1, 0)
        elif event.key == pygame.K_RIGHT: self.app.pan_camera(1, 0)
        
        # Zoom
        elif event.key in (pygame.K_EQUALS, pygame.K_PLUS): self.app.zoom = min(3.0, self.app.zoom + 0.1)
        elif event.key == pygame.K_MINUS: self.app.zoom = max(0.3, self.app.zoom - 0.1)

        # Floor control
        elif event.key == pygame.K_PAGEUP: self.app.change_floor(1)
        elif event.key == pygame.K_PAGEDOWN: self.app.change_floor(-1)

        # Icon selection
        elif pygame.K_0 <= event.key <= pygame.K_9:
            icon_map = [IconType.NONE, IconType.ENTRANCE, IconType.CHEST, IconType.LOCKED_DOOR,
                        IconType.STAIRS_UP, IconType.STAIRS_DOWN, IconType.BOSS, IconType.NPC,
                        IconType.SWITCH, IconType.TRAP]
            self.app.selected_icon = icon_map[event.key - pygame.K_0]

        # Other actions
        elif event.key == pygame.K_l: self.app.start_labelling()
        elif event.key == pygame.K_F11: self.app.toggle_fullscreen()
        elif event.key == pygame.K_k: self.app.toggle_lock_on_selection()
        elif event.key == pygame.K_p: self.app.toggle_player_mode()

    def handle_dialog_input(self, event):
        if event.key == pygame.K_ESCAPE:
            self.app.close_all_dialogs()
        elif self.app.show_save_dialog or self.app.show_load_dialog:
            if event.key == pygame.K_RETURN:
                if self.app.show_save_dialog: self.app.save_map(self.app.file_dialog_text)
                elif self.app.show_load_dialog: self.app.load_map(self.app.file_dialog_text)
                self.app.close_all_dialogs()
            elif event.key == pygame.K_BACKSPACE:
                self.app.file_dialog_text = self.app.file_dialog_text[:-1]
            elif len(self.app.file_dialog_text) < 50 and event.unicode.isprintable():
                self.app.file_dialog_text += event.unicode

    def handle_label_input(self, event):
        if event.key == pygame.K_RETURN:
            if len(self.app.selected_cells) == 1:
                cell = self.app.get_cell(*list(self.app.selected_cells)[0])
                cell.label = self.app.input_text
            self.app.input_mode = False
            self.app.input_text = ""
        elif event.key == pygame.K_ESCAPE:
            self.app.input_mode = False
            self.app.input_text = ""
        elif event.key == pygame.K_BACKSPACE:
            self.app.input_text = self.app.input_text[:-1]
        elif len(self.app.input_text) < 20:
            self.app.input_text += event.unicode

    def handle_ui_click(self, pos):
        # Menu bar
        if config.TITLE_BAR_HEIGHT <= pos[1] < config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT:
            self.handle_menu_bar_click(pos)
            return True
        # Dropdown menus
        if self.app.active_menu:
            if self.handle_dropdown_click(pos):
                return True
        # Icon panel
        if self.app.show_icon_panel and config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT <= pos[1] <= config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT + config.ICON_PANEL_HEIGHT:
            self.handle_icon_panel_click(pos)
            return True
        
        # If a click happened but not on a UI element, close any open menus
        if self.app.active_menu:
            self.app.active_menu = None
        # A click outside UI also clears selection if shift is not held
        if not (pygame.key.get_mods() & pygame.KMOD_SHIFT): self.app.selected_cells.clear()
        return False

    def handle_menu_bar_click(self, pos):
        pos = (pos[0], pos[1] - config.TITLE_BAR_HEIGHT) # Adjust y-coordinate for this bar
        file_text_width = config.SMALL_FONT.render("File", True, config.TEXT_COLOR).get_width()
        help_text_width = config.SMALL_FONT.render("Help", True, config.TEXT_COLOR).get_width()
        
        file_menu_end = 10 + file_text_width + 10
        help_menu_start = file_menu_end + 10
        help_menu_end = help_menu_start + help_text_width + 10

        if 10 <= pos[0] <= file_menu_end:
            self.app.active_menu = 'file' if self.app.active_menu != 'file' else None
        elif help_menu_start <= pos[0] <= help_menu_end:
            self.app.active_menu = 'help' if self.app.active_menu != 'help' else None
        else:
            self.app.active_menu = None

    def handle_dropdown_click(self, pos):
        if self.app.active_menu == 'file':
            dropdown_y = config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT
            items = ["New Map", "Save (Ctrl+S)", "Load (Ctrl+L)", "Quit"]
            if 10 <= pos[0] <= 160 and dropdown_y <= pos[1] <= dropdown_y + len(items) * 25 + 10:
                item_index = (pos[1] - dropdown_y - 5) // 25
                if item_index == 0: self.app.new_map()
                elif item_index == 1: self.app.trigger_save()
                elif item_index == 2: self.app.trigger_load()
                elif item_index == 3: self.app.running = False
                self.app.active_menu = None
                return True
        elif self.app.active_menu == 'help':
            file_text_width = config.SMALL_FONT.render("File", True, config.TEXT_COLOR).get_width()
            dropdown_y = config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT
            dropdown_x = 10 + file_text_width + 20
            items = ["Hotkeys", "About"]
            if dropdown_x <= pos[0] <= dropdown_x + 150 and dropdown_y <= pos[1] <= dropdown_y + len(items) * 25 + 10:
                item_index = (pos[1] - dropdown_y - 5) // 25
                if item_index == 0: self.app.show_hotkeys_dialog = True
                elif item_index == 1: self.app.show_about_dialog = True
                self.app.active_menu = None
                return True
        return False

    def handle_icon_panel_click(self, pos):
        icon_list = [
            IconType.NONE, IconType.ENTRANCE, IconType.CHEST, IconType.LOCKED_DOOR,
            IconType.STAIRS_UP, IconType.STAIRS_DOWN, IconType.BOSS, IconType.NPC,
            IconType.SWITCH, IconType.TRAP
        ]
        icon_x = 10
        icon_size = 50
        panel_y = config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT
        
        if panel_y + 15 <= pos[1] <= panel_y + 15 + icon_size:
            for icon_type in icon_list:
                if icon_x <= pos[0] <= icon_x + icon_size:
                    self.app.selected_icon = icon_type
                    break
                icon_x += icon_size + 10

    def trigger_save_with_dialog(self):
        if HAS_TKINTER:
            root = tk.Tk()
            root.withdraw()
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile="dungeon_map.json"
            )
            root.destroy()
            if filepath:
                self.app.save_map(filepath)
        else:
            self.app.show_save_dialog = True
            self.app.file_dialog_text = "dungeon_map.json"

    def trigger_load_with_dialog(self):
        if HAS_TKINTER:
            root = tk.Tk()
            root.withdraw()
            filepath = filedialog.askopenfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            root.destroy()
            if filepath:
                self.app.load_map(filepath)
        else:
            self.app.show_load_dialog = True
            self.app.file_dialog_text = "dungeon_map.json"