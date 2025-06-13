from PyInstaller.utils.hooks import collect_all, collect_data_files

datas, binaries, hiddenimports = collect_all('streamlit')

# Adiciona imports essenciais que seu app usa
hiddenimports += [
    'streamlit.web.cli',
    'streamlit.runtime.scriptrunner.magic_funcs',
    'requests',
    'bs4',
    'zipfile',
    'io',
    'logging'
]
