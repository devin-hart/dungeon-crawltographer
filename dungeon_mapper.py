import pygame
import math
from typing import Dict, Tuple, Optional, Set

import config
from data_models import Cell, IconType
from renderer import Renderer
from ui import UIManager
from event_handler import EventHandler, HAS_TKINTER
from file_manager import save_map_data, load_map_data

# Initialize Pygame
pygame.init()

class DungeonMapper:
    def __init__(self):
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Dungeon Crawltographer")
        
        self.clock = pygame.time.Clock()
        
        # Window state
        self.window_width = config.WINDOW_WIDTH
        self.window_height = config.WINDOW_HEIGHT
        self.is_fullscreen = False
        
        # Grid state
        self.floors: Dict[int, Dict[Tuple[int, int], Cell]] = {0: {}}
        self.current_floor = 0
        self.current_pos = (config.GRID_SIZE // 2, config.GRID_SIZE // 2)
        self.rotation = 0  # 0, 90, 180, 270
        
        # View state
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # UI state
        self.multi_select_mode = False
        self.selection_start_pos = None
        self.selected_cells: Set[Tuple[int, int]] = set()
        self.selected_icon = IconType.NONE
        self.input_mode = False
        self.input_text = ""
        
        # Menu state
        self.show_icon_panel = True
        self.active_menu = None  # None, 'file', 'help'
        self.show_hotkeys_dialog = False
        self.show_about_dialog = False
        self.show_save_dialog = False
        self.show_load_dialog = False
        self.file_dialog_text = ""
        
        # Mouse drag state
        self.dragging = False
        self.drag_start_pos = None
        self.drag_start_camera = None
        self.left_mouse_down = False
        self.right_mouse_down = False
        self.last_marked_cell = None
        
        # History for undo/redo
        self.history = []
        self.history_index = -1
        self.max_history = 100
        self.current_action = []  # Track cells modified in current drag action

        # Splash screen
        self.splash_image = None
        try:
            self.splash_image = pygame.image.load("splash.png")
        except pygame.error as e:
            print(f"Warning: Could not load splash.png: {e}")
        self.player_mode_enabled = False
        
        self.running = True
        
        # Modular components
        self.renderer = Renderer(self)
        self.ui_manager = UIManager(self)
        self.event_handler = EventHandler(self)

    def get_cell(self, x: int, y: int, floor: int = None) -> Cell:
        """Get or create a cell at the given position"""
        if floor is None:
            floor = self.current_floor
        if floor not in self.floors:
            self.floors[floor] = {}
        if (x, y) not in self.floors[floor]:
            self.floors[floor][(x, y)] = Cell()
        return self.floors[floor][(x, y)]
    
    def screen_to_grid(self, screen_x: int, screen_y: int) -> Optional[Tuple[int, int]]:
        """Convert screen coordinates to grid coordinates"""
        # Adjust for camera and menu bar
        panel_h = config.ICON_PANEL_HEIGHT if self.show_icon_panel else 0
        top_bar_height = config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT
        grid_center_x = self.window_width // 2
        grid_center_y = (self.window_height - top_bar_height - panel_h) // 2 + top_bar_height + panel_h
        
        # Offset from center
        offset_x = (screen_x - grid_center_x) / (config.CELL_SIZE * self.zoom)
        offset_y = (screen_y - grid_center_y) / (config.CELL_SIZE * self.zoom)
        
        # Apply rotation
        angle = math.radians(self.rotation)
        rotated_x = offset_x * math.cos(angle) + offset_y * math.sin(angle)
        rotated_y = -offset_x * math.sin(angle) + offset_y * math.cos(angle)
        
        # Add current position and camera
        grid_x = round(self.current_pos[0] + rotated_x - self.camera_x)
        grid_y = round(self.current_pos[1] + rotated_y - self.camera_y)
        
        return (grid_x, grid_y)
    
    def grid_to_screen(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """Convert grid coordinates to screen coordinates"""
        return self._grid_to_screen_rotated(grid_x, grid_y)

    def grid_to_screen_unrotated(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """
        Convert grid coordinates to screen coordinates, ignoring rotation.
        Useful for drawing UI elements like the selection box that should not rotate with the map.
        """
        return self._grid_to_screen_rotated(grid_x, grid_y, apply_rotation=False)

    def _grid_to_screen_rotated(self, grid_x: int, grid_y: int, apply_rotation: bool = True) -> Tuple[float, float]:
        """Internal helper for grid to screen conversion with optional rotation."""
        panel_h = config.ICON_PANEL_HEIGHT if self.show_icon_panel else 0
        top_bar_height = config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT
        grid_center_x = self.window_width // 2
        grid_center_y = (self.window_height - top_bar_height - panel_h) // 2 + top_bar_height + panel_h
        
        # Offset from current position
        offset_x = grid_x - self.current_pos[0] + self.camera_x
        offset_y = grid_y - self.current_pos[1] + self.camera_y
        
        # Apply rotation
        if apply_rotation:
            angle = math.radians(-self.rotation)
            rotated_x = offset_x * math.cos(angle) + offset_y * math.sin(angle)
            rotated_y = -offset_x * math.sin(angle) + offset_y * math.cos(angle)
        else:
            rotated_x, rotated_y = offset_x, offset_y

        # Convert to screen space
        screen_x = grid_center_x + rotated_x * config.CELL_SIZE * self.zoom
        screen_y = grid_center_y + rotated_y * config.CELL_SIZE * self.zoom
        
        return (screen_x, screen_y)
    
    def save_state(self):
        """Save current state to history for undo/redo"""
        if not self.current_action:
            return
        
        # Remove any history after current index (if we undid and then made new changes)
        self.history = self.history[:self.history_index + 1]
        
        # Add new state
        self.history.append(self.current_action.copy())
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.history_index += 1
        
        self.current_action = []
    
    def undo(self):
        """Undo the last action"""
        if self.history_index < 0:
            return
        
        action = self.history[self.history_index]
        for cell_info in action:
            grid_pos = cell_info['pos']
            prev_state = cell_info['prev']
            
            if prev_state is None:
                # Cell was added, so remove it
                if grid_pos in self.floors[self.current_floor]:
                    del self.floors[self.current_floor][grid_pos]
            else:
                # Cell was modified or removed, restore previous state
                cell = self.get_cell(*grid_pos)
                cell.explored = prev_state['explored']
                cell.icon = prev_state['icon']
                cell.label = prev_state['label']
                cell.locked = prev_state['locked']
        
        self.history_index -= 1
    
    def redo(self):
        """Redo the last undone action"""
        if self.history_index >= len(self.history) - 1:
            return
        
        self.history_index += 1
        action = self.history[self.history_index]
        
        for cell_info in action:
            grid_pos = cell_info['pos']
            new_state = cell_info['new']
            
            if new_state is None:
                # Cell should be removed
                if grid_pos in self.floors[self.current_floor]:
                    del self.floors[self.current_floor][grid_pos]
            else:
                # Cell should be restored/modified
                cell = self.get_cell(*grid_pos)
                cell.explored = new_state['explored']
                cell.icon = new_state['icon']
                cell.label = new_state['label']
                cell.locked = new_state['locked']
    
    def new_map(self):
        """Create a new map, clearing all data"""
        self.floors = {0: {}}
        self.current_floor = 0
        self.current_pos = (config.GRID_SIZE // 2, config.GRID_SIZE // 2)
        self.rotation = 0
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.history = []
        self.history_index = -1
        self.current_action = []
        self.selected_cells.clear()
        print("New map created")

    def handle_click(self, pos: Tuple[int, int], button: int = 1, is_drag: bool = False):
        """Handle mouse click"""
        # Check if clicking in menu bar or icon panel
        if pos[1] < config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT + (config.ICON_PANEL_HEIGHT if self.show_icon_panel else 0):
            return
        
        grid_pos = self.screen_to_grid(*pos)
        if grid_pos:
            if not is_drag: # A normal click clears selection and selects the new cell
                self.selected_cells.clear()
            self.selected_cells.add(grid_pos)
            self.apply_icon_to_selection(button)

    def apply_icon_to_selection(self, button: int = 1):
        """Applies the selected icon or erase action to all selected cells."""
        for grid_pos in self.selected_cells:
            cell = self.get_cell(*grid_pos)
            if cell.locked:
                continue # Skip locked cells

            self._record_cell_change(grid_pos, button)

    def _record_cell_change(self, grid_pos: Tuple[int, int], button: int):
        """Helper to record a single cell change for history and apply it."""
        prev_state = None
        if grid_pos in self.floors[self.current_floor]:
            cell = self.floors[self.current_floor][grid_pos]
            prev_state = {
                'explored': cell.explored,
                'icon': cell.icon,
                'label': cell.label,
                'locked': cell.locked
            }

        if button == 1:  # Left click - add/mark cell
            cell = self.get_cell(*grid_pos)
            cell.explored = True
            cell.icon = self.selected_icon
            new_state = {
                'explored': True,
                'icon': self.selected_icon,
                'label': cell.label,
                'locked': cell.locked
            }
            self.current_action.append({'pos': grid_pos, 'prev': prev_state, 'new': new_state})

        elif button == 3:  # Right click - remove cell
            if grid_pos in self.floors[self.current_floor]:
                del self.floors[self.current_floor][grid_pos]
                self.current_action.append({'pos': grid_pos, 'prev': prev_state, 'new': None})

    def save_map(self, filename: str):
        """Save the current map to a file"""
        save_map_data(filename, self.floors, self.current_floor, self.current_pos, self.rotation)

    def load_map(self, filename: str):
        """Load a map from a file"""
        data = load_map_data(filename)
        if data:
            # Reconstruct cells to ensure they are Cell objects with all attributes
            self.floors = {
                floor: {pos: cell for pos, cell in cells.items()} for floor, cells in data["floors"].items()
            }

            self.current_floor = data["current_floor"]
            self.current_pos = data["current_pos"]
            self.rotation = data["rotation"]
            self.history = []
            self.history_index = -1

    def trigger_save(self):
        self.active_menu = None
        self.event_handler.trigger_save_with_dialog()

    def trigger_load(self):
        self.active_menu = None
        self.event_handler.trigger_load_with_dialog()

    def move_player(self, forward: bool = True):
        """Move the player forward or backward relative to their rotation."""
        direction = -1 if forward else 1
        dx, dy = 0, 0

        if self.rotation == 0: dy = direction
        elif self.rotation == 90: dx = direction
        elif self.rotation == 180: dy = -direction
        elif self.rotation == 270: dx = -direction

        self.current_pos = (self.current_pos[0] + dx, self.current_pos[1] + dy)
        # Mark the new cell as explored
        if self.player_mode_enabled:
            self.get_cell(*self.current_pos).explored = True

    def pan_camera(self, dx, dy):
        if self.rotation == 0: self.camera_x += dx; self.camera_y += dy
        elif self.rotation == 90: self.camera_x += dy; self.camera_y -= dx
        elif self.rotation == 180: self.camera_x -= dx; self.camera_y -= dy
        elif self.rotation == 270: self.camera_x -= dy; self.camera_y += dx

    def change_floor(self, delta: int):
        self.current_floor += delta
        if self.current_floor not in self.floors:
            self.floors[self.current_floor] = {}

    def start_labelling(self):
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[1] > config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT + (config.ICON_PANEL_HEIGHT if self.show_icon_panel else 0):
            grid_pos = self.screen_to_grid(*mouse_pos)
            if grid_pos:
                # If multiple cells are selected, don't start labelling
                if len(self.selected_cells) == 1:
                    selected_pos = list(self.selected_cells)[0]
                    cell = self.get_cell(*selected_pos)
                    if cell.explored and not cell.locked:
                        self.input_mode = True
                        self.input_text = cell.label

    def toggle_lock_on_selection(self):
        """Toggles the locked state for all selected cells."""
        if not self.selected_cells:
            return

        # Determine the new state from the first cell
        first_cell = self.get_cell(*list(self.selected_cells)[0])
        new_locked_state = not first_cell.locked

        for grid_pos in self.selected_cells:
            self.get_cell(*grid_pos).locked = new_locked_state
        
    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.RESIZABLE)
        self.window_width = self.screen.get_width()
        self.window_height = self.screen.get_height()

    def toggle_player_mode(self):
        """Toggle player mode on or off."""
        self.player_mode_enabled = not self.player_mode_enabled

    def is_dialog_open(self):
        return self.show_hotkeys_dialog or self.show_about_dialog or self.show_save_dialog or self.show_load_dialog

    def close_all_dialogs(self):
        self.show_hotkeys_dialog = False
        self.show_about_dialog = False
        self.show_save_dialog = False
        self.show_load_dialog = False
        self.file_dialog_text = ""

    def draw(self):
        self.screen.fill(config.BG_COLOR)
        self.renderer.draw_grid()
        self.ui_manager.draw_ui()
        self.ui_manager.draw_dialogs()
        self.ui_manager.draw_input_prompt()
        pygame.display.flip()

    def show_splash(self):
        """Display the splash screen for a few seconds."""
        if not self.splash_image:
            return

        scaled_image = pygame.transform.scale(self.splash_image, (500, 500))

        self.screen.fill(config.BG_COLOR)
        splash_rect = scaled_image.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(scaled_image, splash_rect)
        pygame.display.flip()
        pygame.time.wait(3000) # Wait for 3 seconds

    def run(self):
        """Main game loop"""
        self.show_splash()

        while self.running:
            self.clock.tick(60)

            # Handle events
            self.event_handler.handle_events()
            
            # Draw
            self.draw()
        
        pygame.quit()

if __name__ == "__main__":
    mapper = DungeonMapper()
    mapper.run()