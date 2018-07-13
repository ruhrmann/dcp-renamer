# dcp-renamer
DCP-Renamer is a program to rename Digital Cinema Packages

It runs with Python 2.7. To use it install python 2.7 and run "python dcp-renamer.py" or you could try to use th dcp_renamer.exe for windows 64bit. It was created with pyinstaller. Needs a few seconds to start.

# known bugs
* does not work if no `<OriginalFileName>`-Tag is present in PKL an CPL-Files (which is the case for DCPs created with DCP-O-Matic)
  
# features for next versions
* FilmTitle-Wizard creating DCDN-compliant names: http://isdcf.com/dcnc/

