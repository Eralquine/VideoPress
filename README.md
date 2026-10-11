# VideoPress

Aplicación de escritorio con interfaz gráfica (Tkinter) para **comprimir videos en lote usando ffmpeg**. A pesar del nombre, no gestiona publicación/streaming de video: es un compresor local de archivos MP4/video.

## Qué hace

- Permite agregar archivos individuales (`*.mp4`) o carpetas completas (busca recursivamente `*.mp4`) a una lista de trabajo.
- Comprime cada archivo con `ffmpeg` usando codec de video `libx264` y audio `aac` (128k), con `-movflags +faststart`.
- Parámetros configurables desde la UI:
  - **CRF** (calidad, 18–51; 18 = alta calidad, 28 = media, 40+ = baja/más compresión).
  - **Preset de codificación** (`ultrafast` → `veryslow`, balance velocidad/compresión).
  - **Carpeta de salida** (si no se especifica, usa la misma carpeta del archivo original).
  - **Sufijo** del archivo de salida (por defecto `_compressed`).
  - **Sobrescribir** archivo de salida si ya existe.
- Procesa los archivos en un hilo (`threading`) separado para no bloquear la UI.
- Muestra progreso en tiempo real por archivo: parsea la salida de `ffmpeg` (frame, fps, tiempo transcurrido, velocidad) con una expresión regular para calcular porcentaje completado y tiempo restante estimado.
- Usa `ffprobe` para obtener la duración del video de origen y así calcular el progreso.
- Mantiene un log con timestamps de cada paso (info, éxito, advertencia, error).
- Al terminar cada archivo, muestra el tamaño original vs. comprimido y el porcentaje de reducción; acumula el total de espacio ahorrado en el lote.
- Permite detener el procesamiento en curso (botón "DETENER"), terminando el proceso de `ffmpeg` activo.
- Si `ffmpeg.exe`/`ffprobe.exe` no se encuentran junto a la aplicación, lo indica en la UI y bloquea el inicio de la compresión.

## Cómo funciona internamente

- Un único archivo: `video_compressor.py`.
- Clase principal `VideoCompressor(tk.Tk)` construye toda la interfaz (panel de archivos, panel de configuración, log y controles inferiores) y maneja el estado de la cola de archivos.
- Espera encontrar los binarios `ffmpeg.exe` y `ffprobe.exe` en el mismo directorio que el script (o, si está empaquetado con PyInstaller, dentro de `sys._MEIPASS`). Es decir, está pensado para ejecutarse en **Windows** junto a esos dos ejecutables (no usa `ffmpeg`/`ffprobe` del `PATH` del sistema, y usa `CREATE_NO_WINDOW` propio de Windows).
- No incluye los binarios de `ffmpeg`/`ffprobe` en el repo: deben colocarse manualmente en el mismo directorio del script/ejecutable.

## Requisitos

- Python 3 con Tkinter disponible.
- `ffmpeg.exe` y `ffprobe.exe` ubicados en el mismo directorio que `video_compressor.py`.
- Probado/diseñado para Windows (usa banderas específicas de `subprocess` de Windows).

## Uso

```bash
python video_compressor.py
```

1. Agrega archivos con "+ Archivo" o una carpeta completa con "+ Carpeta" (se buscan `*.mp4` recursivamente).
2. (Opcional) Elige carpeta de salida, ajusta CRF, preset y sufijo.
3. Pulsa "▶ INICIAR COMPRESIÓN".
4. Sigue el progreso en la lista de archivos y en el log inferior.

## Estructura del repositorio

```
video_compressor.py   # Aplicación completa (UI + lógica de compresión)
```

No hay dependencias externas de Python declaradas (`requirements.txt`), tests, ni archivos de configuración/empaquetado en el repositorio.
