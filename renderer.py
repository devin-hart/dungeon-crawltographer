import pygame
import math

from data_models import IconType
import config

class Renderer:
    def __init__(self, app):
        self.app = app
        self.screen = app.screen

    def draw_grid(self):
        """Draw the grid and cells"""
        grid_range = 40
        size = config.CELL_SIZE * self.app.zoom

        for x in range(-grid_range, grid_range + 1):
            for y in range(-grid_range, grid_range + 1):
                grid_x = self.app.current_pos[0] + x
                grid_y = self.app.current_pos[1] + y

                screen_x, screen_y = self.app.grid_to_screen(grid_x, grid_y)

                y_min = config.MENU_BAR_HEIGHT + (config.ICON_PANEL_HEIGHT if self.app.show_icon_panel else 0)
                if -size <= screen_x <= self.app.window_width + size and y_min - size <= screen_y <= self.app.window_height + size:
                    rect = pygame.Rect(int(screen_x - size/2), int(screen_y - size/2), int(size), int(size))
                    pygame.draw.rect(self.screen, config.GRID_COLOR, rect, 1)

        # Pass 1: Draw cell backgrounds and icons
        if self.app.current_floor in self.app.floors:
            for (x, y), cell in self.app.floors[self.app.current_floor].items():
                if cell.explored:
                    screen_x, screen_y = self.app.grid_to_screen(x, y)
                    if -size <= screen_x <= self.app.window_width + size and -size <= screen_y <= self.app.window_height + size:
                        rect = pygame.Rect(int(screen_x - size/2), int(screen_y - size/2), int(size), int(size))
                        pygame.draw.rect(self.screen, config.EXPLORED_COLOR, rect)
                        pygame.draw.rect(self.screen, config.GRID_COLOR, rect, 1)
                        if cell.icon != IconType.NONE:
                            self.draw_icon(cell.icon, screen_x, screen_y, size)
                        if cell.locked:
                            self.draw_lock_icon(screen_x, screen_y, size)

        self._draw_selection_highlight()

        # Pass 2: Draw labels on top of everything else
        if self.app.current_floor in self.app.floors:
            for (x, y), cell in self.app.floors[self.app.current_floor].items():
                if cell.explored and cell.label:
                    screen_x, screen_y = self.app.grid_to_screen(x, y)
                    size = config.CELL_SIZE * self.app.zoom
                    if -size <= screen_x <= self.app.window_width + size and -size <= screen_y <= self.app.window_height + size:
                        if cell.label:
                            label_surf = config.SMALL_FONT.render(cell.label, True, config.TEXT_COLOR)
                            label_bg = pygame.Surface((label_surf.get_width() + 4, label_surf.get_height() + 2))
                            label_bg.fill(config.LABEL_BG_COLOR[:3])
                            label_bg.set_alpha(200)
                            label_y = screen_y - (size / 2) - label_surf.get_height() - 4
                            self.screen.blit(label_bg, (screen_x - label_surf.get_width()//2 - 2, label_y - 2))
                            self.screen.blit(label_surf, (screen_x - label_surf.get_width()//2, label_y))

        screen_x, screen_y = self.app.grid_to_screen(*self.app.current_pos)
        pygame.draw.circle(self.screen, config.CURRENT_POS_COLOR, (int(screen_x), int(screen_y)), int(size * 0.4))

        end_x = screen_x
        end_y = screen_y - size * 0.6
        pygame.draw.line(self.screen, config.CURRENT_POS_COLOR, (screen_x, screen_y), (end_x, end_y), 3)

        self._draw_selection_box()

    def _draw_selection_highlight(self):
        """Draw a highlight over selected cells."""
        if not self.app.selected_cells:
            return

        size = config.CELL_SIZE * self.app.zoom
        highlight_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        highlight_surface.fill(config.SELECTION_COLOR)

        for grid_pos in self.app.selected_cells:
            screen_x, screen_y = self.app.grid_to_screen(*grid_pos)
            self.screen.blit(highlight_surface, (screen_x - size/2, screen_y - size/2))

    def _draw_selection_box(self):
        """Draw the multi-select box when dragging."""
        if not self.app.multi_select_mode or not self.app.selection_start_pos:
            return

        mouse_pos = pygame.mouse.get_pos()
        start_screen_pos = self.app.grid_to_screen_unrotated(*self.app.selection_start_pos)
        
        width = mouse_pos[0] - start_screen_pos[0]
        height = mouse_pos[1] - start_screen_pos[1]

        rect = pygame.Rect(start_screen_pos[0], start_screen_pos[1], width, height)
        pygame.draw.rect(self.screen, config.SELECTION_BOX_COLOR, rect, 2)


    def draw_icon(self, icon_type: IconType, x: float, y: float, size: float):
        """Draw an icon at the given screen position"""
        s = size * 0.7 # Use a slightly larger icon scale

        if icon_type == IconType.ENTRANCE:
            # A simple green 'E'
            color = (80, 220, 80)
            pygame.draw.line(self.screen, color, (x - s/2, y - s/2), (x - s/2, y + s/2), int(s/8)) # Vertical bar
            pygame.draw.line(self.screen, color, (x - s/2, y - s/2), (x + s/3, y - s/2), int(s/8)) # Top bar
            pygame.draw.line(self.screen, color, (x - s/2, y), (x + s/4, y), int(s/8)) # Middle bar
            pygame.draw.line(self.screen, color, (x - s/2, y + s/2), (x + s/3, y + s/2), int(s/8)) # Bottom bar

        elif icon_type == IconType.CHEST:
            # A simple treasure chest
            chest_color = (160, 82, 45) # Sienna
            lock_color = (255, 215, 0) # Gold
            body_rect = pygame.Rect(x - s/2, y - s/4, s, s/2)
            pygame.draw.rect(self.screen, chest_color, body_rect, border_radius=int(s/12))
            pygame.draw.rect(self.screen, (0,0,0), body_rect, 1, border_radius=int(s/12)) # Outline
            pygame.draw.circle(self.screen, lock_color, (x, y), s/8)

        elif icon_type == IconType.LOCKED_DOOR:
            # A simple key
            key_color = (200, 200, 200)
            pygame.draw.circle(self.screen, key_color, (x, y - s/4), s/4)
            pygame.draw.line(self.screen, key_color, (x, y - s/8), (x, y + s/2), int(s/10))
            pygame.draw.line(self.screen, key_color, (x, y + s/2), (x - s/4, y + s/2), int(s/10))

        elif icon_type == IconType.STAIRS_UP:
            # Green triangle pointing up
            points = [(x, y - s/2), (x + s/2, y + s/2), (x - s/2, y + s/2)]
            pygame.draw.polygon(self.screen, (80, 220, 80), points)

        elif icon_type == IconType.STAIRS_DOWN:
            # Red triangle pointing down
            points = [(x, y + s/2), (x + s/2, y - s/2), (x - s/2, y - s/2)]
            pygame.draw.polygon(self.screen, (220, 80, 80), points)

        elif icon_type == IconType.BOSS:
            # A red circle
            pygame.draw.circle(self.screen, (220, 50, 50), (x, y), s/2)

        elif icon_type == IconType.NPC:
            # A green circle
            pygame.draw.circle(self.screen, (50, 220, 50), (x, y), s/2)

        elif icon_type == IconType.SWITCH:
            # Gray box with a black button
            pygame.draw.rect(self.screen, (150, 150, 150), (x - s/2, y - s/2, s, s), border_radius=int(s/8))
            pygame.draw.circle(self.screen, (0, 0, 0), (x, y), s/4)

        elif icon_type == IconType.TRAP:
            # A yellow exclamation point
            color = (255, 220, 50)
            pygame.draw.rect(self.screen, color, (x - s/10, y - s/2, s/5, s/2), border_radius=int(s/10))
            pygame.draw.circle(self.screen, color, (x, y + s/3), s/8)

        elif icon_type == IconType.SAVE_POINT:
            pts = [(x, y-s/2), (x+s/2, y), (x, y+s/2), (x-s/2, y)]
            pygame.draw.polygon(self.screen, (80, 240, 220), pts)
            pygame.draw.polygon(self.screen, (180, 255, 240), pts, 2)
            pygame.draw.line(self.screen, (255, 255, 255), (x, y-s/3), (x, y+s/3), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (x-s/3, y), (x+s/3, y), 2)

    def draw_lock_icon(self, x: float, y: float, size: float):
        """Draw a small padlock icon on a cell."""
        s = size * 0.3 # Make the square a decent size
        lock_color = (255, 255, 255) # White
        
        # Position in top-left corner of the cell
        px, py = x - size/2 + 2, y - size/2 + 2 # Add a small padding

        pygame.draw.rect(self.screen, lock_color, (px, py, s, s))