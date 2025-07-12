from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('scipy')

# Modules specifiques souvent manques
hiddenimports += collect_submodules('scipy.stats')
hiddenimports += collect_submodules('scipy.special')
hiddenimports += collect_submodules('scipy._lib')

# Imports specifiques qui causent des problemes
hiddenimports += [
    'scipy._lib.messagestream',
    'scipy.special._ufuncs',
    'scipy.special._ufuncs_cxx',
    'scipy.stats._stats',
    'scipy.stats._continuous_distns',
    'scipy.stats._discrete_distns'
]
