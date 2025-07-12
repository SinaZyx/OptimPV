from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('seaborn')

# Matplotlib backends
hiddenimports += [
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_agg'
]
