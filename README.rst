rypak provides lossless file size reduction for various file types

**Supported file types**

builtin support for the following file types:

- MS office open xml files (docx, pptx, xlsx)
- zip files
- tar files: will create a compressed zip file with same contents

additional files types are supported with external utilities:

- png files, if optipng.exe is present
- jpg files, if jpegtran.exe is present
- h5 files, if h5repack.exe is present
- bmp, gif, tif files: will create smaller png file of same image (optipng)

Embedded png and jpg media in OOXML files will be optimized if the
corresponding utility is available.

**External Utilities**

7-Zip <http://www.7-zip.org/>
  : 7-Zip provides a ZIP compression ratio that is 2-10% better than the
  ratio provided by PKZip and WinZip.

OptiPNG <http://optipng.sourceforge.net/>
  : OptiPNG is a PNG optimizer that recompresses image files to a smaller
  size, without losing any information.

jpegtran.exe <http://jpegclub.org/jpegtran/>
  : jpegtran performs various lossless transformations of JPEG files.

h5repack.exe <https://www.hdfgroup.org/HDF5/doc/RM/Tools.html>
  : Copies an HDF5 file to a new file with or without compression and/or
  chunking. 
