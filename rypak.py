"""
Lossless file size reduction of various file types

Author: JR Rygg
"""
__author__ = "J. R. Rygg"
__version__ = "0.1 alpha"

import shutil
import tempfile
import zipfile

#============================= BODY ========================================
def unpack(sourcezip):
    """Extract files from .zip to temp directory and return path to tempdir."""
    tempdir = tempfile.mkdtemp()
    with zipfile.ZipFile(sourcezip, 'r') as ziphandle:
        ziphandle.extractall(tempdir)
    return tempdir

#============================= MAIN ===========================================
def main():
    pass

if __name__ == '__main__':
    main()
