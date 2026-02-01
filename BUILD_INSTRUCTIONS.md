# Guía de Construcción y Exportación - Antigravity Downmess

Esta guía explica cómo generar la aplicación ejecutable para diferentes sistemas operativos.

## 1. Windows (Ya Generado)

El ejecutable `.exe` ya ha sido creado y se encuentra en la carpeta `dist/` dentro de este directorio.

- **Archivo**: `dist/Antigravity_Downloader.exe`
- **Uso**: Simplemente doble clic para ejecutar. No requiere instalación de Python.

---

## 2. macOS (`.app` / `.dmg`)

**IMPORTANTE**: Para crear una aplicación de macOS, **DEBES** realizar el proceso desde un ordenador Mac. No es posible crear un `.app` funcional desde Windows.

### Pasos para Mac

1. **Copiar Archivos**: Copia la carpeta de este proyecto a tu Mac.
2. **Instalar Python**: Asegúrate de tener Python 3 instalado (se recomienda usar `brew install python`).
3. **Instalar Dependencias**:
    Abre la terminal en la carpeta del proyecto y ejecuta:

    ```bash
    pip3 install customtkinter yt-dlp pillow plyer pyinstaller
    ```

4. **Compilar**:
    Ejecuta el siguiente comando en la terminal:

    ```bash
    pyinstaller --noconfirm --onefile --windowed --name "Antigravity_Downloader" --icon "downmess.ico" --hidden-import "PIL._tkinter_finder" --hidden-import "PIL" --hidden-import "ctypes" --hidden-import "customtkinter" downmess.py
    ```

5. **Resultado**: Tu aplicación estará en la carpeta `dist/`.

---

## 3. Android (`.apk`)

**ESTADO ACTUAL**: No Compatible Directamente.

### Explicación Técnica

La aplicación actual está construida con **CustomTkinter** y `tkinter`. Estas librerías gráficas están diseñadas exclusivamente para sistemas de escritorio (Windows, Mac, Linux) y **no funcionan en Android ni iOS**.

### Solución Futura

Para tener esta aplicación en un móvil, sería necesario **reescribir la interfaz gráfica** utilizando un framework compatible con móviles, como:

1. **Flet** (Python): Permite crear apps multiplataforma (Móvil, Web, Desktop) con Python.
2. **Kivy** (Python): El estándar clásico para apps móviles en Python.
3. **React Native / Flutter**: Si se decide salir de Python para la interfaz.

El *núcleo* de la lógica (`downmess_core.py`) es reutilizable, pero toda la parte visual (`downmess.py`) tendría que hacerse de nuevo para adaptarse a pantallas táctiles y al sistema Android.
