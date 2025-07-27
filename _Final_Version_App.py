import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from io import BytesIO
from PIL import Image, ImageTk
import sqlite3
import os



class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tooltip or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tooltip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#ffffe0", relief="solid", borderwidth=1,
                         font=("Segoe UI", 10))
        label.pack(ipadx=5, ipady=2)

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


API_KEY = "9ce5863249031d8bba636830e7a2b331"
HEADERS = {"User-Agent": "weather-app"}

favorites = {
    "Москва": (55.7558, 37.6173),
    "Париж": (48.8566, 2.3522),
    "Токио": (35.6895, 139.6917),
}

THEMES = {
    "light": {
        "bg": "#d0e7f9",
        "fg": "black",
        "entry_bg": "white",
        "button_bg": "#e6f2ff",
    },
    "dark": {
        "bg": "#222222",
        "fg": "white",
        "entry_bg": "#555555",
        "button_bg": "#444444",
    }
}

icon_cache = {}


DB_FILE = "favorites.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            city TEXT PRIMARY KEY,
            lat REAL,
            lon REAL
        )
    """)
    conn.commit()
    conn.close()

def load_favorites():
    if not os.path.exists(DB_FILE):
        return {}
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT city, lat, lon FROM favorites")
    result = {city: (lat, lon) for city, lat, lon in cursor.fetchall()}
    conn.close()
    return result



def load_icon_from_api(icon_code):
    if icon_code in icon_cache:
        return icon_cache[icon_code]
    url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        image_data = response.content
        image = Image.open(BytesIO(image_data))
        photo = ImageTk.PhotoImage(image)
        icon_cache[icon_code] = photo
        return photo
    except Exception as e:
        print(f"Ошибка загрузки иконки {icon_code}: {e}")
        return None

def search_cities(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 10}
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

def fetch_weather(lat, lon):
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru",
    }
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

def fetch_current_weather(lat, lon):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru",
    }
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

def deg_to_dir(deg):
    if deg is None:
        return "—"
    dirs = ['С', 'СВ', 'В', 'ЮВ', 'Ю', 'ЮЗ', 'З', 'СЗ']
    return dirs[int((deg + 22.5) / 45) % 8]

def clear_frame(frame):
    for w in frame.winfo_children():
        w.destroy()

def format_dt(dt_txt):
    dt = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%d.%m %H:%M"), dt.date()

root = tk.Tk()
root.title("Погода")
root.geometry("900x750")

theme = tk.StringVar(value="light")

def apply_theme(widget=None):
    if widget is None:
        widget = root
    colors = THEMES[theme.get()]
    bg, fg = colors["bg"], colors["fg"]
    entry_bg = colors["entry_bg"]
    btn_bg = colors["button_bg"]

    cls = widget.__class__.__name__
    try:
        if cls == "Entry":
            widget.configure(bg=entry_bg, fg=fg, insertbackground=fg)
        elif cls == "Button":
            widget.configure(bg=btn_bg, fg=fg, activebackground=btn_bg)
        elif cls == "Canvas":
            widget.configure(bg=bg)
        elif cls == "Frame":
            widget.configure(bg=bg)
        elif cls == "Label":
            widget.configure(bg=bg, fg=fg)
        elif cls == "OptionMenu":
            widget.configure(bg=btn_bg, fg=fg)
        elif cls == "Scrollbar":
            widget.configure(bg=bg)
        elif cls == "Notebook":
            widget.configure(bg=bg)
        else:
            widget.configure(bg=bg, fg=fg)
    except:
        pass
    for child in widget.winfo_children():
        apply_theme(child)

# --- UI setup ---

top_frame = tk.Frame(root)
top_frame.pack(fill="x", padx=10, pady=5)

city_entry = tk.Entry(top_frame, font=("Segoe UI", 11), width=50)
city_entry.pack(side="left", fill="x", expand=True)

cities = []

def on_search():
    q = city_entry.get().strip()
    if not q:
        messagebox.showinfo("Информация", "Введите название города")
        return
    global cities
    cities = search_cities(q)
    city_listbox.delete(0, tk.END)
    for c in cities:
        city_listbox.insert(tk.END, c.get('display_name'))

search_button = tk.Button(top_frame, text="Найти", font=("Segoe UI", 11), command=on_search)
search_button.pack(side="left", padx=5)

def toggle_theme():
    theme.set("dark" if theme.get() == "light" else "light")
    apply_theme()

theme_btn = tk.Button(top_frame, text="Сменить тему", command=toggle_theme)
theme_btn.pack(side="left", padx=5)

def add_favorite():
    city_name = coords_label.cget("text").split(",")[0]
    if city_name and coords_label.lat is not None and coords_label.lon is not None:
        favorites[city_name] = (coords_label.lat, coords_label.lon)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO favorites (city, lat, lon) VALUES (?, ?, ?)",
                       (city_name, coords_label.lat, coords_label.lon))
        conn.commit()
        conn.close()

        update_favorites_tabs()
        messagebox.showinfo("Избранное", f"Город '{city_name}' добавлен в избранное.")


fav_btn = tk.Button(top_frame, text="Добавить в избранное", command=add_favorite)
fav_btn.pack(side="left", padx=5)

fav_frame = tk.Frame(root)
fav_frame.pack(fill="x", padx=10)

notebook = ttk.Notebook(fav_frame)
notebook.pack(fill="x")

def show_weather_for_favorite(lat, lon):
    # Получаем имя города из favorites
    for name, (lt, ln) in favorites.items():
        if lt == lat and ln == lon:
            coords_label.config(text=name)
            coords_label.lat = lat
            coords_label.lon = lon
            break
    threading.Thread(target=lambda: show_weather(lat, lon), daemon=True).start()


def close_tab(event):
    x, y = event.x, event.y
    elem = notebook.identify(x, y)
    if "label" not in elem:
        return
    index = notebook.index(f"@{x},{y}")
    city_name = notebook.tab(index, "text")
    if city_name in favorites:
        if messagebox.askyesno("Удалить из избранного", f"Удалить город '{city_name}' из избранного?"):
            del favorites[city_name]

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM favorites WHERE city = ?", (city_name,))
            conn.commit()
            conn.close()

            update_favorites_tabs()


def update_favorites_tabs():
    for tab_id in notebook.tabs():
        notebook.forget(tab_id)
    for city_name, (lat, lon) in favorites.items():
        frame = tk.Frame(notebook)
        notebook.add(frame, text=city_name)
        btn = tk.Button(frame, text=f"Показать погоду: {city_name}",
                        command=lambda lt=lat, ln=lon: show_weather_for_favorite(lt, ln))
        btn.pack(fill="x")
    notebook.bind("<Button-3>", close_tab)

init_db()
favorites = load_favorites()
update_favorites_tabs()


city_listbox = tk.Listbox(root, font=("Segoe UI", 10), height=5)
city_listbox.pack(fill="x", padx=10)
city_listbox.config(width=0)

coords_label = tk.Label(root, text="Город не выбран", font=("Segoe UI", 12, "bold"))
coords_label.pack(padx=10, pady=5, anchor="w")
coords_label.lat = None
coords_label.lon = None

def on_city_select(ev):
    sel = city_listbox.curselection()
    if not sel:
        return
    city = cities[sel[0]]
    coords_label.config(text=city['display_name'])
    coords_label.lat = float(city['lat'])
    coords_label.lon = float(city['lon'])
    threading.Thread(target=lambda: show_weather(coords_label.lat, coords_label.lon), daemon=True).start()

city_listbox.bind("<<ListboxSelect>>", on_city_select)

forecast_container = tk.Frame(root)
forecast_container.pack(fill="both", expand=True, padx=10, pady=5)

canvas_forecast = tk.Canvas(forecast_container, highlightthickness=0)
scrollbar_forecast = ttk.Scrollbar(forecast_container, orient="vertical", command=canvas_forecast.yview)
canvas_forecast.configure(yscrollcommand=scrollbar_forecast.set)

scrollbar_forecast.pack(side="right", fill="y")
canvas_forecast.pack(side="left", fill="both", expand=True)

weather_forecast_frame = tk.Frame(canvas_forecast)
weather_forecast_frame.bind(
    "<Configure>",
    lambda e: canvas_forecast.configure(scrollregion=canvas_forecast.bbox("all"))
)

canvas_forecast.create_window((0, 0), window=weather_forecast_frame, anchor="nw")

def _on_mousewheel(event):
    if event.delta:
        canvas_forecast.yview_scroll(-1 * int(event.delta / 120), "units")
    elif event.num == 4:
        canvas_forecast.yview_scroll(-1, "units")
    elif event.num == 5:
        canvas_forecast.yview_scroll(1, "units")

def bind_mousewheel(widget):
    widget.bind_all("<MouseWheel>", _on_mousewheel)
    widget.bind_all("<Button-4>", _on_mousewheel)
    widget.bind_all("<Button-5>", _on_mousewheel)

bind_mousewheel(root)

graph_container = tk.Frame(root)
graph_container.pack(fill="both", expand=False, padx=10, pady=5)

graph_frame = tk.Frame(graph_container)
graph_frame.pack(fill="both", expand=True)

def plot_temperature(data):
    clear_frame(graph_frame)
    dates = []
    temps = []
    for dt_str, item in data:
        dates.append(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"))
        temps.append(item["main"]["temp"])

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(dates, temps, marker='o')
    ax.set_title("Температура на ближайшие дни")
    ax.set_ylabel("°C")
    ax.grid(True)
    fig.autofmt_xdate()

    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def clear_weather():
    clear_frame(weather_forecast_frame)
    clear_frame(graph_frame)
    for w in current_label.winfo_children():
        w.destroy()
    current_label.config(text="")

current_label = tk.Label(root, font=("Segoe UI", 12, "bold"), anchor="w", justify="left")
current_label.pack(fill="x", padx=10)

def show_weather(lat, lon):
    clear_weather()
    current = fetch_current_weather(lat, lon)
    forecast = fetch_weather(lat, lon)
    if current is None or forecast is None:
        messagebox.showerror("Ошибка", "Не удалось получить данные о погоде")
        return

    # Отображение текущей погоды
    icon_code = current['weather'][0]['icon']
    icon_img = load_icon_from_api(icon_code)
    for w in current_label.winfo_children():
        w.destroy()

    pressure_hpa = current['main']['pressure']
    pressure_mmHg = round(pressure_hpa * 0.75006)

    txt = (
        f"{current['name']}, {current['sys']['country']}\n"
        f"Погода: {current['weather'][0]['description'].capitalize()}\n"
        f"Температура: {current['main']['temp']} °C\n"
        f"Ветер: {current['wind']['speed']} м/с, {deg_to_dir(current['wind'].get('deg'))}\n"
        f"Влажность: {current['main']['humidity']}%\n"
        f"Давление: {pressure_mmHg} мм рт.ст.\n"
    )

    if icon_img:
        label_icon = tk.Label(current_label, image=icon_img, bg=THEMES[theme.get()]['bg'])
        label_icon.image = icon_img
        label_icon.pack(side="left", padx=10)
    label_text = tk.Label(current_label, text=txt, justify="left",
                          bg=THEMES[theme.get()]['bg'], fg=THEMES[theme.get()]['fg'])
    label_text.pack(side="left")

    # Прогноз погоды
    clear_frame(weather_forecast_frame)
    forecast_list = forecast['list']
    current_date = None
    day_frame = None

    for item in forecast_list:
        dt_str = item['dt_txt']
        dt_formatted, dt_date = format_dt(dt_str)

        if dt_date != current_date:
            current_date = dt_date
            day_frame = tk.LabelFrame(weather_forecast_frame,
                                      text=dt_date.strftime("%d.%m.%Y"),
                                      bg=THEMES[theme.get()]['bg'],
                                      fg=THEMES[theme.get()]['fg'],
                                      font=("Segoe UI", 14, "bold"))

            day_frame.pack(fill="x", pady=15)


        icon_code = item['weather'][0]['icon']
        icon_img = load_icon_from_api(icon_code)
        temp = item['main']['temp']
        desc = item['weather'][0]['description'].capitalize()
        wind_speed = item['wind']['speed']
        wind_dir = deg_to_dir(item['wind'].get('deg'))
        hum = item['main']['humidity']

        item_frame = tk.Frame(day_frame, bg=THEMES[theme.get()]['bg'])
        item_frame.pack(fill="x", padx=15, pady=8)


        time_label = tk.Label(item_frame, text=dt_formatted, width=10,
                              bg=THEMES[theme.get()]['bg'], fg=THEMES[theme.get()]['fg'],
                              font=("Segoe UI", 12, "bold"))
        time_label.pack(side="left")

        if icon_img:
            icon_label = tk.Label(item_frame, image=icon_img, bg=THEMES[theme.get()]['bg'])
            icon_label.image = icon_img
            icon_label.pack(side="left", padx=5)
        else:
            icon_label = None  # На всякий случай

        # Левая колонка — основная информация
        left_info_frame = tk.Frame(item_frame, bg=THEMES[theme.get()]['bg'])
        left_info_frame.pack(side="left", fill="x", expand=True)

        info_main = f"{temp} °C, {desc}, Ветер: {wind_speed} м/с {wind_dir}, Влажность: {hum}%"
        info_label = tk.Label(left_info_frame, text=info_main, anchor="w",
                              bg=THEMES[theme.get()]['bg'], fg=THEMES[theme.get()]['fg'],
                              font=("Segoe UI", 12))
        info_label.pack(anchor="w")

        # Данные для подсказки
        pressure_mmHg = int(item['main'].get('pressure', 0) * 0.75006) if 'pressure' in item['main'] else '—'
        visibility = item.get('visibility', '—')
        pop = int(float(item.get('pop', 0)) * 100)

        tooltip_text = (
            f"Давление: {pressure_mmHg} мм рт.ст.\n"
            f"Видимость: {visibility} м\n"
            f"Осадки: {pop}%"
        )

        # Создаем один общий Tooltip для item_frame
        tooltip = Tooltip(item_frame, tooltip_text)

        # Привязываем к icon_label события для показа/скрытия той же подсказки
        if icon_label:
            icon_label.unbind("<Enter>")
            icon_label.unbind("<Leave>")

            icon_label.bind("<Enter>", lambda e, t=tooltip: t.show())
            icon_label.bind("<Leave>", lambda e, t=tooltip: t.hide())

    # График температур
    plot_temperature([(item['dt_txt'], item) for item in forecast_list])




apply_theme()
root.mainloop()

