import pygame

import config
from data_models import IconType
from renderer import Renderer

class UIManager:
    def __init__(self, app):
        self.app = app
        self.screen = app.screen
        self.renderer = Renderer(app) # For drawing icons in the UI

    def draw_ui(self):
        """Draw the menu bar and icon panel"""
        self._draw_title_bar()
        self._draw_menu_bar()
        if self.app.show_icon_panel:
            self._draw_icon_panel()
        self._draw_dropdown_menus()
        self._draw_hover_tooltip()

    def _draw_title_bar(self):
        pygame.draw.rect(self.screen, config.UI_BG_COLOR, (0, 0, self.app.window_width, config.TITLE_BAR_HEIGHT))
        pygame.draw.line(self.screen, config.GRID_COLOR, (0, config.TITLE_BAR_HEIGHT), (self.app.window_width, config.TITLE_BAR_HEIGHT), 1)
        title_surf = config.SMALL_FONT.render("Dungeon Crawltographer", True, config.TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(self.app.window_width / 2, config.TITLE_BAR_HEIGHT / 2))
        self.screen.blit(title_surf, title_rect)

    def _draw_menu_bar(self):
        bar_y = config.TITLE_BAR_HEIGHT
        pygame.draw.rect(self.screen, config.UI_BG_COLOR, (0, bar_y, self.app.window_width, config.MENU_BAR_HEIGHT))
        pygame.draw.line(self.screen, config.GRID_COLOR, (0, bar_y + config.MENU_BAR_HEIGHT), (self.app.window_width, bar_y + config.MENU_BAR_HEIGHT), 1)

        menu_x = 10
        file_text = config.SMALL_FONT.render("File", True, config.TEXT_COLOR)
        file_rect = pygame.Rect(menu_x, bar_y + 5, file_text.get_width() + 10, 20)
        if self.app.active_menu == 'file':
            pygame.draw.rect(self.screen, config.BUTTON_HOVER_COLOR, file_rect)
        self.screen.blit(file_text, (menu_x + 5, bar_y + 8))
        menu_x += file_text.get_width() + 20

        help_text = config.SMALL_FONT.render("Help", True, config.TEXT_COLOR)
        help_rect = pygame.Rect(menu_x, bar_y + 5, help_text.get_width() + 10, 20)
        if self.app.active_menu == 'help':
            pygame.draw.rect(self.screen, config.BUTTON_HOVER_COLOR, help_rect)
        self.screen.blit(help_text, (menu_x + 5, bar_y + 8))

    def _draw_icon_panel(self):
        panel_y = config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT
        pygame.draw.rect(self.screen, config.UI_BG_COLOR, (0, panel_y, self.app.window_width, config.ICON_PANEL_HEIGHT))
        pygame.draw.line(self.screen, config.GRID_COLOR, (0, panel_y + config.ICON_PANEL_HEIGHT), (self.app.window_width, panel_y + config.ICON_PANEL_HEIGHT), 1)

        icon_list = [
            (IconType.NONE, "0"), (IconType.ENTRANCE, "1"), (IconType.CHEST, "2"),
            (IconType.LOCKED_DOOR, "3"), (IconType.STAIRS_UP, "4"), (IconType.STAIRS_DOWN, "5"),
            (IconType.BOSS, "6"), (IconType.NPC, "7"), (IconType.SWITCH, "8"), (IconType.TRAP, "9"),
        ]

        icon_x = 10
        icon_size = 40
        for icon_type, key in icon_list:
            color = config.SELECTION_BOX_COLOR if self.app.selected_icon == icon_type else config.BUTTON_COLOR
            button_rect = pygame.Rect(icon_x, panel_y + 5, icon_size, icon_size)
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, config.GRID_COLOR, button_rect, 1)

            if icon_type != IconType.NONE:
                self.renderer.draw_icon(icon_type, icon_x + icon_size/2, panel_y + 5 + icon_size/2, icon_size)
            else:
                pygame.draw.line(self.screen, config.TEXT_COLOR, (icon_x + 8, panel_y + 13), (icon_x + icon_size - 8, panel_y + icon_size - 3), 2)
                pygame.draw.line(self.screen, config.TEXT_COLOR, (icon_x + icon_size - 8, panel_y + 13), (icon_x + 8, panel_y + icon_size - 3), 2)

            key_surf = config.SMALL_FONT.render(key, True, config.TEXT_COLOR)
            self.screen.blit(key_surf, (icon_x + icon_size//2 - key_surf.get_width()//2, panel_y + 45))
            icon_x += icon_size + 5

        # Draw status info on the right side of the icon panel
        player_mode_status = "ON" if self.app.player_mode_enabled else "OFF"
        info_text = f"Floor: {self.app.current_floor} | Pos: ({self.app.current_pos[0]}, {self.app.current_pos[1]}) | Rot: {self.app.rotation}° | Zoom: {self.app.zoom:.1f}x | Player Mode: {player_mode_status}"
        info_surf = config.SMALL_FONT.render(info_text, True, config.TEXT_COLOR)
        self.screen.blit(info_surf, (self.app.window_width - info_surf.get_width() - 10, panel_y + (config.ICON_PANEL_HEIGHT - info_surf.get_height()) // 2))

    def _draw_dropdown_menus(self):
        if self.app.active_menu == 'file':
            dropdown_x = 10
            dropdown_y = config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT
            dropdown_items = ["New Map", "Save (Ctrl+S)", "Save As...", "Load (Ctrl+L)", "Quit"]
            self._draw_dropdown(dropdown_x, dropdown_y, 150, dropdown_items)
        elif self.app.active_menu == 'help':
            file_text_width = config.SMALL_FONT.render("File", True, config.TEXT_COLOR).get_width()
            dropdown_x = 10 + file_text_width + 20
            dropdown_y = config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT
            dropdown_items = ["Hotkeys", "About"]
            self._draw_dropdown(dropdown_x, dropdown_y, 150, dropdown_items)

    def _draw_dropdown(self, x, y, width, items):
        height = len(items) * 25 + 10
        pygame.draw.rect(self.screen, config.UI_BG_COLOR, (x, y, width, height))
        pygame.draw.rect(self.screen, config.GRID_COLOR, (x, y, width, height), 1)

        mouse_pos = pygame.mouse.get_pos()
        for i, item in enumerate(items):
            item_y = y + 5 + i * 25
            item_rect = pygame.Rect(x + 5, item_y, width - 10, 20)
            if item_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, config.BUTTON_HOVER_COLOR, item_rect)
            item_surf = config.SMALL_FONT.render(item, True, config.TEXT_COLOR)
            self.screen.blit(item_surf, (x + 10, item_y + 2))

    def _draw_hover_tooltip(self):
        """Draws a tooltip for a cell label when the mouse hovers over it."""
        mouse_pos = pygame.mouse.get_pos()

        # Do not draw tooltips if a menu is open or if dragging
        if self.app.active_menu or self.app.dragging or self.app.left_mouse_down or self.app.right_mouse_down:
            return

        # Check if mouse is over the grid area
        panel_h = config.ICON_PANEL_HEIGHT if self.app.show_icon_panel else 0
        top_bar_height = config.TITLE_BAR_HEIGHT + config.MENU_BAR_HEIGHT
        if mouse_pos[1] <= top_bar_height + panel_h:
            return

        grid_pos = self.app.screen_to_grid(*mouse_pos)
        if not grid_pos:
            return

        # Check if a cell exists at this position and has a label
        if self.app.current_floor in self.app.floors and grid_pos in self.app.floors[self.app.current_floor]:
            cell = self.app.get_cell(*grid_pos)
            if cell.label:
                label_surf = config.FONT.render(cell.label, True, config.TEXT_COLOR)
                tooltip_rect = pygame.Rect(mouse_pos[0] + 15, mouse_pos[1] + 10, label_surf.get_width() + 10, label_surf.get_height() + 6)
                pygame.draw.rect(self.screen, config.UI_BG_COLOR, tooltip_rect)
                pygame.draw.rect(self.screen, config.GRID_COLOR, tooltip_rect, 1)
                self.screen.blit(label_surf, (tooltip_rect.x + 5, tooltip_rect.y + 3))

    def draw_dialogs(self):
        """Draw dialog windows"""
        if self.app.show_hotkeys_dialog:
            self._draw_hotkeys_dialog()
        elif self.app.show_about_dialog:
            self._draw_about_dialog()
        elif self.app.show_save_dialog:
            self._draw_file_dialog("Save Map")
        elif self.app.show_load_dialog:
            self._draw_file_dialog("Load Map")

    def _draw_hotkeys_dialog(self):
        hotkeys = [
            ("General", ""),
            ("Ctrl+S", "Save map"),
            ("Ctrl+L", "Load map"),
            ("Ctrl+Z / Ctrl+Y", "Undo / Redo"),
            ("F11", "Toggle Fullscreen"),
            ("ESC", "Close dialog or menu"),
            ("", ""),
            ("Map Interaction", ""),
            ("Left Click", "Select a single cell"),
            ("Ctrl + Left Click", "Apply icon to selected cell(s)"),
            ("Ctrl + Drag", "Fill cells with selected icon"),
            ("Shift + Drag", "Select multiple cells"),
            ("Alt + Drag Selection", "Move selected cells"),
            ("Right Click / Drag", "Erase cells"),
            ("Middle Mouse Drag", "Pan the map view"),
            ("Mouse Wheel", "Zoom in / out"),
            ("L", "Add/Edit cell label"),
            ("K", "Toggle lock on selected cells"),
            ("0-9", "Select icon (0-9)"),
            ("", ""),
            ("Navigation", ""),
            ("W / S", "Move player forward / backward"),
            ("A / D", "Rotate player left / right"),
            ("H", "Warp player to entrance"),
            ("Arrow Keys", "Pan the map view"),
            ("Page Up / Page Down", "Change floor"),
            ("P", "Toggle Player Mode")
        ]

        # Dynamically calculate dialog height
        dialog_width = 500
        base_height = 80 # For title and padding
        heading_height = 28
        item_height = 22
        separator_height = 10
        
        content_height = sum(
            separator_height if not k and not d else (heading_height if not d else item_height)
            for k, d in hotkeys
        )
        dialog_height = base_height + content_height

        dialog_x = (self.app.window_width - dialog_width) // 2
        dialog_y = (self.app.window_height - dialog_height) // 2

        pygame.draw.rect(self.screen, config.UI_BG_COLOR, (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, config.TEXT_COLOR, (dialog_x, dialog_y, dialog_width, dialog_height), 2)

        title = config.FONT.render("Hotkeys", True, config.TEXT_COLOR)
        self.screen.blit(title, (dialog_x + 20, dialog_y + 20))

        y = dialog_y + 60
        for key, desc in hotkeys:
            if not key and not desc:
                y += 10 # Add extra space for a separator
                continue
            if not desc: # This is a heading
                text = config.FONT.render(key, True, config.TEXT_COLOR)
                self.screen.blit(text, (dialog_x + 25, y))
                y += 28
            else:
                key_surf = config.SMALL_FONT.render(key, True, (200, 200, 100))
                desc_surf = config.SMALL_FONT.render(desc, True, config.TEXT_COLOR)
                self.screen.blit(key_surf, (dialog_x + 40, y))
                self.screen.blit(desc_surf, (dialog_x + 200, y))
                y += 22

    def _draw_about_dialog(self):
        dialog_width, dialog_height = 400, 200
        dialog_x = (self.app.window_width - dialog_width) // 2
        dialog_y = (self.app.window_height - dialog_height) // 2

        pygame.draw.rect(self.screen, config.UI_BG_COLOR, (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, config.TEXT_COLOR, (dialog_x, dialog_y, dialog_width, dialog_height), 2)

        title = config.FONT.render("About", True, config.TEXT_COLOR)
        self.screen.blit(title, (dialog_x + 20, dialog_y + 20))

        lines = [
            ("Dungeon Mapper", config.TEXT_COLOR, 70),
            ("Vibe coded by Devin Hart", config.TEXT_COLOR, 100),
            ("https://devinh.art", (100, 150, 255), 125),
            ("Press ESC to close", config.TEXT_COLOR, 160)
        ]

        for text, color, y_offset in lines:
            line_surf = config.SMALL_FONT.render(text, True, color)
            self.screen.blit(line_surf, (dialog_x + 30, dialog_y + y_offset))

    def _draw_file_dialog(self, title_text: str):
        dialog_width, dialog_height = 500, 150
        dialog_x = (self.app.window_width - dialog_width) // 2
        dialog_y = (self.app.window_height - dialog_height) // 2

        pygame.draw.rect(self.screen, config.UI_BG_COLOR, (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, config.TEXT_COLOR, (dialog_x, dialog_y, dialog_width, dialog_height), 2)

        title = config.FONT.render(title_text, True, config.TEXT_COLOR)
        self.screen.blit(title, (dialog_x + 20, dialog_y + 20))

        prompt = config.SMALL_FONT.render("Filename:", True, config.TEXT_COLOR)
        self.screen.blit(prompt, (dialog_x + 30, dialog_y + 60))

        input_rect = pygame.Rect(dialog_x + 120, dialog_y + 58, 340, 25)
        pygame.draw.rect(self.screen, config.BG_COLOR, input_rect)
        pygame.draw.rect(self.screen, config.TEXT_COLOR, input_rect, 1)

        input_text = config.SMALL_FONT.render(self.app.file_dialog_text + "_", True, config.TEXT_COLOR)
        self.screen.blit(input_text, (dialog_x + 125, dialog_y + 62))

        action = "save" if "Save" in title_text else "load"
        inst = config.SMALL_FONT.render(f"Press ENTER to {action}, ESC to cancel", True, config.TEXT_COLOR)
        self.screen.blit(inst, (dialog_x + 30, dialog_y + 110))

    def draw_input_prompt(self):
        if self.app.input_mode:
            prompt_text = config.FONT.render(f"Label: {self.app.input_text}_", True, config.TEXT_COLOR)
            prompt_bg = pygame.Surface((prompt_text.get_width() + 20, prompt_text.get_height() + 10))
            prompt_bg.fill(config.UI_BG_COLOR)
            prompt_x = self.app.window_width // 2 - prompt_text.get_width() // 2
            prompt_y = self.app.window_height - 60
            self.screen.blit(prompt_bg, (prompt_x - 10, prompt_y - 5))
            self.screen.blit(prompt_text, (prompt_x, prompt_y))