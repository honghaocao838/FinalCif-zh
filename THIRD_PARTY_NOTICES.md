# Third-party notices

This repository is a Chinese localization of FinalCif by Honghao Cao (honghaocao838@gmail.com). It contains the upstream
source code plus localization changes, and the Windows installer bundles the
runtime libraries required by FinalCif.

## FinalCif

Original application, version 180. Author: Daniel Kratzert, dkratzert@gmx.de.
License: Beer-Ware (Revision 42), see `LICENSE.md`.

## PLATON

`platon/platon_special.exe` and the alert definitions in `check.def` come from
PLATON by Anthony L. Spek (Utrecht University), <https://www.platonsoft.nl/xraysoft>.
PLATON is free of charge for academic use. For-profit organizations need a
license from the author.

`check.def` is not versioned in this repository (`*.def` is ignored); the
installer build downloads it from the official server. Chinese translations of
the alert explanations are provided by this project in
`finalcif/datafiles/checkdef_zh.json` and are attributed to PLATON.

## fastmolwidget

Version 1.5.1, MIT license. Bundled in the Windows installer as part of the
FinalCif runtime. The installer build translates the residual-density toolbar
labels by replacing string constants in the installed bytecode.

## Qt for Python (PySide6)

LGPLv3. Bundled in the Windows installer as part of the FinalCif runtime
(unmodified Qt libraries). Source and license: <https://www.qt.io/qt-for-python>.

## Python

Python 3.14 runtime, PSF License. Bundled unmodified in the Windows installer.
