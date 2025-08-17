from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_all, collect_submodules

# Collecter TOUTES les données de Streamlit
datas, binaries, hiddenimports = collect_all('streamlit')

# Ajouter les métadonnées (CRITIQUE pour l'erreur "No package metadata")
datas += copy_metadata("streamlit")
datas += copy_metadata("altair")
datas += copy_metadata("pandas")
datas += copy_metadata("numpy")
datas += copy_metadata("pyarrow")

# Altair
datas += collect_data_files("altair")

# Ajouter TOUS les imports cachés nécessaires
hiddenimports += [
    # Core Streamlit
    "streamlit.web.cli",
    "streamlit.runtime.scriptrunner.magic_funcs",
    "streamlit.web.server.websocket_headers",
    "streamlit.runtime.legacy_caching.caching",
    "streamlit.runtime.caching",
    "streamlit.runtime.state",
    "streamlit.delta_generator",
    "streamlit.elements",
    "streamlit.components.v1",
    "streamlit.__main__",
    
    # Web server
    "streamlit.web.server",
    "streamlit.web.server.server",
    "streamlit.web.server.routes",
    "streamlit.web.server.browser_websocket_handler",
    
    # Dependencies
    "altair.vegalite.v4",
    "pyarrow.compute",
    "pyarrow.parquet",
    "pyarrow.lib",
    "pyarrow._compute",
    "tornado.web",
    "tornado.ioloop",
    "tornado.websocket",
    
    # Additional
    "click",
    "validators", 
    "packaging",
    "toml",
    "gitpython",
    "pympler",
    "cachetools",
    "typing_extensions",
    "blinker",
    "protobuf",
    "watchdog",
    "watchdog.observers",
    "watchdog.events"
]

# S'assurer que tous les sous-modules sont inclus
hiddenimports += collect_submodules('streamlit')
