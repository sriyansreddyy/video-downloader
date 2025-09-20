import PyInstaller.__main__

PyInstaller.__main__.run([
    'video_downloader.py',
    '--name=VideoDownloader',
    '--onefile',
    '--windowed',
    '--add-data=logo.png;.',
    '--hidden-import=ssl',
    '--hidden-import=_ssl',
    '--hidden-import=yt_dlp',
    '--hidden-import=tkinterdnd2',
    '--hidden-import=PIL',
])
