from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_all

datas = []
binaries = []
hiddenimports = []

# Streamlit
datas += copy_metadata("streamlit")
datas += collect_data_files("streamlit")

# Altair
datas += collect_data_files("altair")

# Ajouter les imports caches
hiddenimports += [
    "streamlit.runtime.scriptrunner.magic_funcs",
    "streamlit.web.server.websocket_headers",
    "streamlit.runtime.legacy_caching.caching",
    "streamlit.runtime.caching",
    "altair.vegalite.v4",
    "pyarrow.compute",
    "pyarrow.parquet",
    "tornado.web",
    "tornado.ioloop"
]
