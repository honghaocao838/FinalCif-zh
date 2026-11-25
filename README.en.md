English | [简体中文](README.md)

# FinalCif Chinese Edition

Chinese localization of [FinalCif](https://github.com/dkratzert/FinalCif).

## Download and installation

Download `FinalCif-zh-v180-setup-x64.exe` from [Releases](https://github.com/honghaocao838/FinalCif-zh/releases) and run it.

- Installs per user, no administrator rights required
- Windows 10/11 x64
- Both the setup wizard and the application are in Chinese
- Open `.cif`, `.res` or `.hkl` files, or drop them onto the window

## What FinalCIF does

FinalCIF is a CIF file editor for single-crystal X-ray diffraction data.

- Collects cell, space group, completeness and R values from SHELX, SADABS and similar files
- Table-based CIF editing with templates and data-source comparison
- Built-in CheckCIF (offline PLATON or online IUCr); PLAT alerts show explanations
- Structure reports (Word/HTML), ADP tables, molecule plots
- PLATON SQUEEZE / Olex2 solvent masks, twinning, absolute configuration

Changes in this edition:

- Chinese user interface, messages and dialogs
- Column hints above the main table; tooltips on headers and CIF keys
- Main-table filters for status, Chinese aliases, required items and CheckCIF mentions, plus a format-error summary
- Online CheckCIF shows elapsed time, failure reasons and alert counts; requests can be cancelled and the server connection tested
- Chinese explanations for all 545 PLAT alerts, with the official English text appended; IUCr prefilter checks get Chinese rules and fix advice
- Chinese help texts for the CIF dictionary (all 1,429 items), including type and limits
- Upstream auto-update disabled; updates are published in this repository
- Generated CIF files and report text remain in English

## License and credits

- FinalCif: Daniel Kratzert, Beer-Ware (Revision 42), see [LICENSE](LICENSE)
- Chinese localization: Honghao Cao, under the same Beer-Ware terms
- Third-party components (PLATON, fastmolwidget, PySide6): see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

## Contact

Honghao Cao, honghaocao838@gmail.com. Please use e-mail or the issue tracker.

## Upstream

https://github.com/dkratzert/FinalCif
