
import flet as ft
from downmess_core import DownmessCore
import threading
import os
import webbrowser
import time

# --- Constants & Theme (Messrack Luxury Tech) ---
MESS_OBSIDIAN = "#0F0F0F"    # Deep background
MESS_MATTE = "#1A1A1A"       # Cards / Surface
MESS_GOLD = "#D4AF37"        # Primary Accent / Text Highlight
MESS_STEEL = "#4A4A4A"       # Borders / Inactive
MESS_TEXT_MAIN = "#E0E0E0"   # Main Text (off-white)
MESS_TEXT_DIM = "#B0B0B0"    # Secondary Text

def check_permissions():
    """Request necessary permissions on Android"""
    try:
        from plyer import permission
        permission.request_permissions([
            permission.READ_EXTERNAL_STORAGE, 
            permission.WRITE_EXTERNAL_STORAGE
        ])
    except:
        pass

def main(page: ft.Page):
    # Setup Page
    page.title = "Downmess Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = MESS_OBSIDIAN
    page.padding = 10
    page.window_width = 400
    page.window_height = 800
    page.scroll = "auto"
    
    # Configure global fonts if available, otherwise fallback to default
    page.fonts = {
        "Montserrat": "https://fonts.gstatic.com/s/montserrat/v25/JTUSjIg1_i6t8kCHKm459Wlhyw.ttf",
        "Roboto": "https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxK.ttf"
    }
    page.theme = ft.Theme(font_family="Roboto")
    
    # Run permissions check
    check_permissions()

    # Core will be initialized lazily or on first use to prevent blocking
    core = DownmessCore()

    # --- UI HELPERS ---
    def MessButton(text, icon_name=None, on_click=None, is_primary=False, width=None):
        content_list = []
        icon_color = MESS_OBSIDIAN if is_primary else MESS_GOLD
        text_color = MESS_OBSIDIAN if is_primary else MESS_GOLD
        
        if icon_name:
            content_list.append(ft.Icon(icon_name, color=icon_color, size=18))
        content_list.append(ft.Text(text, color=text_color, weight=ft.FontWeight.BOLD, font_family="Montserrat", spacing=2)) # Tracking simulation
        
        return ft.Container(
            content=ft.Row(content_list, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            bgcolor=MESS_GOLD if is_primary else "transparent",
            border=None if is_primary else ft.border.all(1, MESS_GOLD),
            padding=ft.padding.symmetric(vertical=15, horizontal=20),
            border_radius=4, # Small radius (Luxury Tech rule 5)
            on_click=on_click,
            width=width,
            alignment=ft.Alignment(0, 0),
            ink=True,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.colors.with_opacity(0.1, MESS_GOLD),
                offset=ft.Offset(0, 0),
                blur_style=ft.ShadowBlurStyle.OUTER,
            ) if not is_primary else None
        )

    def create_card(title, content_list, icon_name=None):
        header_content = []
        if icon_name: 
            header_content.append(ft.Icon(icon_name, color=MESS_GOLD, size=20))
        header_content.append(ft.Text(title.upper(), size=16, weight=ft.FontWeight.BOLD, color=MESS_GOLD, font_family="Montserrat", spacing=2))
        
        return ft.Container(
            content=ft.Column([
                ft.Row(header_content, alignment=ft.MainAxisAlignment.START, spacing=10),
                ft.Container(height=1, bgcolor=MESS_STEEL, margin=ft.Margin(top=5, bottom=15)),
                ft.Column(content_list, spacing=20)
            ]),
            bgcolor=MESS_MATTE,
            padding=25,
            border_radius=8,
            border=ft.border.all(1, "#222"), # Very subtle border
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color="black",
                offset=ft.Offset(0, 4),
            ),
            margin=ft.Margin(bottom=15)
        )

    def safe_update():
        try: page.update()
        except: pass

    def show_snack(msg, color=MESS_GOLD):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color=MESS_OBSIDIAN, weight=ft.FontWeight.BOLD),
            bgcolor=color, 
            open=True
        )
        safe_update()

    # --- 1. DOWNLOADER ---
    # Styling Inputs
    def StyledTextField(label, multiline=False, min_lines=1, width=None, hint_text=None):
        return ft.TextField(
            label=label, 
            hint_text=hint_text,
            border_color=MESS_STEEL, 
            focused_border_color=MESS_GOLD,
            cursor_color=MESS_GOLD,
            text_style=ft.TextStyle(color=MESS_TEXT_MAIN),
            label_style=ft.TextStyle(color=MESS_TEXT_DIM),
            multiline=multiline,
            min_lines=min_lines,
            width=width,
            border_radius=4,
            bgcolor=ft.colors.with_opacity(0.3, "black")
        )

    current_url = StyledTextField(label="URLs (Una por línea)", multiline=True, min_lines=3)
    
    quality_dropdown = ft.Dropdown(
        label="Calidad",
        options=[
            ft.dropdown.Option("Mejor Calidad (4K/8K)"),
            ft.dropdown.Option("1080p"), 
            ft.dropdown.Option("720p"), 
            ft.dropdown.Option("Solo Audio (MP3 320kbps)")
        ],
        value="1080p",
        border_color=MESS_STEEL,
        focused_border_color=MESS_GOLD,
        text_style=ft.TextStyle(color=MESS_TEXT_MAIN),
        label_style=ft.TextStyle(color=MESS_TEXT_DIM),
        bgcolor=MESS_MATTE,
        border_radius=4
    )
    
    # Time Range Inputs
    start_time = StyledTextField(label="Inicio (MM:SS)", width=150)
    end_time = StyledTextField(label="Fin (MM:SS)", width=150)
    
    normalize_switch = ft.Switch(label="Normalizar", value=True, active_color=MESS_GOLD, active_track_color=MESS_STEEL)
    auto_paste_switch = ft.Switch(label="Auto-Paste", value=False, active_color=MESS_GOLD, active_track_color=MESS_STEEL)

    dl_progress = ft.ProgressBar(color=MESS_GOLD, bgcolor=MESS_STEEL, visible=False, border_radius=0)
    status_text = ft.Text(size=12, color=MESS_TEXT_DIM, font_family="Roboto")

    def run_dl(e):
        raw_urls = current_url.value
        if not raw_urls: 
            status_text.value = "Link requerido"
            safe_update()
            return
        
        urls = [u.strip() for u in raw_urls.split('\n') if u.strip()]
        status_text.value = f"Iniciando descarga de {len(urls)} videos..."
        dl_progress.visible = True
        safe_update()
        
        def _t():
            try:
                for url in urls:
                    core.download_url(url, quality_dropdown.value, 
                                     normalize=normalize_switch.value,
                                     start_time=start_time.value if start_time.value else None,
                                     end_time=end_time.value if end_time.value else None)
                status_text.value = "¡Todas las descargas completadas!"
                show_snack("Proceso Finalizado")
            except Exception as ex:
                status_text.value = f"Error: {ex}"
            finally:
                dl_progress.visible = False
                safe_update()
                refresh_history()
        threading.Thread(target=_t, daemon=True).start()
    
    downloader_view = [
        create_card("Descargador", [
            current_url,
            quality_dropdown,
            ft.Row([start_time, end_time], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([normalize_switch, auto_paste_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            MessButton("EJECUTAR DESCARGAS", "download", on_click=run_dl, is_primary=True),
            dl_progress,
            status_text
        ], "download")
    ]

    # --- 2. SEARCH ---
    search_query = StyledTextField(label=None, hint_text="Buscar música...")
    engine_dd = ft.Dropdown(
        options=[ft.dropdown.Option("YouTube"), ft.dropdown.Option("SoundCloud")],
        value="YouTube",
        width=140,
        border_color=MESS_STEEL,
        focused_border_color=MESS_GOLD,
        text_style=ft.TextStyle(color=MESS_TEXT_MAIN),
        bgcolor=MESS_MATTE,
        dense=True,
        border_radius=4
    )
    search_results = ft.Column()

    def run_search(e):
        q = search_query.value
        if not q: return
        search_results.controls.clear()
        search_results.controls.append(ft.Container(content=ft.ProgressRing(color=MESS_GOLD), alignment=ft.alignment.center))
        safe_update()
        
        def _t():
            try:
                engine_code = "scsearch" if engine_dd.value == "SoundCloud" else "ytsearch"
                res = core.search_videos(q, limit=10, engine=engine_code)
                search_results.controls.clear()
                for v in res:
                    search_results.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Image(src=v['thumbnail'], width=100, height=60, fit=ft.ImageFit.COVER, border_radius=4) if v.get('thumbnail') else ft.Icon("play_arrow", color=MESS_GOLD),
                                ft.Column([
                                    ft.Text(v['title'][:40], weight=ft.FontWeight.BOLD, color=MESS_TEXT_MAIN, size=13, font_family="Roboto"),
                                    ft.Text(f"{v.get('uploader','?')}", size=11, color=MESS_TEXT_DIM)
                                ], expand=True),
                                ft.IconButton(icon="add", icon_color=MESS_GOLD, on_click=lambda e, u=v['url']: transfer(u))
                            ]),
                            bgcolor=ft.colors.with_opacity(0.05, "white"), padding=10, border_radius=4, margin=ft.Margin(bottom=5),
                            border=ft.border.only(left=ft.BorderSide(2, MESS_GOLD))
                        )
                    )
            except Exception as ex:
                search_results.controls.append(ft.Text(str(ex), color="red"))
            safe_update()
        threading.Thread(target=_t, daemon=True).start()

    search_view = [
        create_card("Buscador", [
            ft.Row([
                ft.Container(search_query, expand=True),
                ft.Container(
                    ft.IconButton(icon="search", icon_color=MESS_OBSIDIAN, on_click=run_search),
                    bgcolor=MESS_GOLD, border_radius=4
                )
            ]),
            engine_dd
        ], "search"),
        search_results
    ]

    # --- 3. AI TOOLS ---
    ai_status = ft.Text(size=12, color=MESS_GOLD)
    ai_progress = ft.ProgressBar(color=MESS_GOLD, bgcolor=MESS_STEEL, visible=False, border_radius=0)
    
    def run_ai_task(task_type, file_path):
        if not file_path: 
            ai_status.value = "Selecciona un archivo"
            safe_update()
            return
        
        ai_status.value = f"Procesando {task_type}..."
        ai_progress.visible = True
        safe_update()
        
        def _t():
            try:
                if task_type == "Resize":
                    out = core.resize_image(file_path, 1920, 1080)
                elif task_type == "Upscale":
                    out = core.upscale_image_ai(file_path, scale=2)
                elif task_type == "BG Remove":
                    out = core.remove_background(file_path)
                ai_status.value = f"¡Éxito!: {os.path.basename(out)}"
                show_snack(f"{task_type} Completado")
            except Exception as ex:
                ai_status.value = f"Error: {ex}"
            finally:
                ai_progress.visible = False
                safe_update()
        threading.Thread(target=_t, daemon=True).start()

    # Mobile path input
    ai_path = StyledTextField(label="Ruta de Imagen")
    
    ai_view = [
        create_card("Herramientas IA", [
            ai_path,
            ft.Row([
                MessButton("RESIZE", on_click=lambda e: run_ai_task("Resize", ai_path.value), width=100),
                MessButton("UPSCALE", on_click=lambda e: run_ai_task("Upscale", ai_path.value), width=100),
            ], alignment=ft.MainAxisAlignment.CENTER),
            MessButton("QUITAR FONDO", on_click=lambda e: run_ai_task("BG Remove", ai_path.value), is_primary=True),
            ai_progress,
            ai_status
        ], "auto_awesome")
    ]

    # --- 4. HISTORY ---
    history_col = ft.Column()
    def refresh_history():
        history_col.controls.clear()
        try:
            h = core.load_history()
            for i in h:
                history_col.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(i.get('title', '???'), weight=ft.FontWeight.BOLD, color=MESS_TEXT_MAIN, size=13),
                            ft.Text(f"{i.get('date','')} | {i.get('quality','')}", size=11, color=MESS_TEXT_DIM)
                        ]),
                        padding=12, 
                        border=ft.border.only(bottom=ft.BorderSide(1, MESS_STEEL)),
                    )
                )
        except: pass
        safe_update()

    history_view = [
        create_card("Historial", [history_col], "history")
    ]

    # --- NAVIGATION ---
    def transfer(url):
        current_url.value = (current_url.value + "\n" + url).strip()
        nav_bar.selected_index = 0
        change_tab(0)

    def change_tab(idx_or_e):
        idx = idx_or_e if isinstance(idx_or_e, int) else idx_or_e.control.selected_index
        page.clean()
        
        if idx == 0: page.controls.extend(downloader_view)
        elif idx == 1: page.controls.extend(search_view)
        elif idx == 2: page.controls.extend(ai_view)
        elif idx == 3: 
            refresh_history()
            page.controls.extend(history_view)
            
        page.add(nav_bar)
        safe_update()

    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon="download", label="Inicio"),
            ft.NavigationBarDestination(icon="search", label="Buscar"),
            ft.NavigationBarDestination(icon="auto_awesome", label="IA"),
            ft.NavigationBarDestination(icon="history", label="Historial"),
        ],
        on_change=change_tab,
        bgcolor=MESS_MATTE,
        indicator_color=MESS_GOLD,
        icon_content_color=MESS_TEXT_DIM,
        label_behavior=ft.NavigationBarLabelBehavior.ONLY_SHOW_SELECTED
    )
    
    page.navigation_bar = nav_bar
    page.controls.extend(downloader_view)
    page.update()

    # Clipboard Monitor Loop
    def clipboard_monitor():
        last_clip = ""
        while True:
            # Placeholder for Flet clipboard logic
            time.sleep(3)

if __name__ == "__main__":
    ft.app(target=main)
