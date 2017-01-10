"""Lossless file size reduction of various file types

File types currently supported:
    zip, pptx, xlsx, docx, h5, png, jpg
    tar => creates a compressed zip with same info
    bmp, gif, tif => creates png version of same image
"""
__author__ = "J. Ryan Rygg"
__version__ = "0.5 beta"

import argparse
import datetime
from glob import glob
import os
import os.path as osp
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

# paths to helper utility executables
utilities = ('7z', 'optipng', 'jpegtran', 'h5repack')
UTIL_EXE = {}
for uname in utilities:
    path = shutil.which(uname)
    if path is not None:
        UTIL_EXE[uname] = path

# list of accepted extensions, and paths to OOXML media
OOXML_MEDIA = {
    '.docx': osp.join('word', 'media'),
    '.pptx': osp.join('ppt', 'media'),
    '.xlsx': osp.join('xl', 'media'),
}
ZIP_TYPE = tuple(OOXML_MEDIA.keys()) + ('.zip',)
JPG_TYPE = ('.jpg', '.jpeg', '.jpe')
OPTIPNG_ALT_TYPE = ('.bmp', '.gif', '.tif', '.tiff')
ACCEPTED_TYPES = list(ZIP_TYPE + ('.tar',))

if 'optipng' in UTIL_EXE:
    ACCEPTED_TYPES.append('.png')
    ACCEPTED_TYPES.extend(OPTIPNG_ALT_TYPE)
if 'jpegtran' in UTIL_EXE:
    ACCEPTED_TYPES.extend(JPG_TYPE)
if 'h5repack' in UTIL_EXE:
    ACCEPTED_TYPES.append('.h5')

#============================= BODY ==========================================
BYTE_SUFFIXES = ['B', 'kiB', 'MiB', 'GiB', 'TiB']
def humansize(nbytes):
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(BYTE_SUFFIXES)-1:
        nbytes /= 1024.0
        i += 1
    return "{:.2f} {}".format(nbytes, BYTE_SUFFIXES[i])


def print_oneline_summary(label, size1, size2):
    ratio = 100 * (size2 / size1 - 1)
    diff = humansize(size1 - size2)
    sys.stdout.write("{} ... {} to {} ({:.2f}%) [diff = {}]\n".format(
        label, humansize(size1), humansize(size2), ratio, diff))


def optimize_png(src, dst):
    """Optimize jpg file using jpegtran."""
    args = [UTIL_EXE.get('optipng', None)]
    if args[0] is None:
        return
    args.extend(('-o5', '-preserve', '-out', dst))
    args.append(src)
    subprocess.run(args)


def optimize_jpg(src, dst, extra_markers='all'):
    """Optimize jpg file using jpegtran."""
    args = [UTIL_EXE.get('jpegtran', None)]
    if args[0] is None:
        return
    args.extend(('-optimize', '-progressive', '-copy', extra_markers))
    args.extend((src, dst))
    subprocess.run(args)


def h5repack(src, dst, options=('-f', 'GZIP=9')):
    """Repack hdf5 files using h5repack.exe"""
    args = [UTIL_EXE.get('h5repack', None)]
    if args[0] is None:
        return
    args.extend(options)
    args.extend((src, dst))
    subprocess.run(args)


class UnpackedZip():
    """A context manager. Returns path to temp directory w/ files from zip."""
    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        self.tempdir = tempfile.mkdtemp()
        with zipfile.ZipFile(self.filename, 'r') as zf:
            zf.extractall(self.tempdir)
        return self.tempdir

    def __exit__(self, *args):
        shutil.rmtree(self.tempdir)


def repack_folder(sourcedir, dst):
    """Pack sourcedir into dst .zip archive"""
    if '7z' in UTIL_EXE:
        # a: Add files to archive
        # -tzip: "zip" Type archive
        # -mx9: compression Method x9 (max)
        args = [UTIL_EXE.get('7z', None)]
        if args[0] is None:
            return
        args.extend(['a', '-tzip', dst, osp.join(sourcedir,'*'), '-mx9'])
        subprocess.call(args, stdout=subprocess.PIPE)
    else:
        root = osp.abspath(sourcedir)
        with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zf:
            for dirname, subdirs, files in os.walk(sourcedir):
                zf.write(dirname, osp.relpath(dirname, root))
                for filename in files:
                    arcname = osp.join(osp.relpath(dirname, root), filename)
                    zf.write(osp.join(dirname, filename), arcname)


def repack_zip(sourcename, destname):
    """Repak a zipfile."""
    if '7z' in UTIL_EXE:
        with UnpackedZip(sourcename) as tempdir:
            repack_folder(tempdir, destname)
    else: # use python builtin zipfile package if 7z not available
        with zipfile.ZipFile(sourcename, 'r') as src:
            with zipfile.ZipFile(destname, 'w') as dst:
                for n, i in zip(src.namelist(), src.infolist()):
                    dst.writestr(i, src.read(n), zipfile.ZIP_DEFLATED)


def repack_ooxml(sourcename, destname):
    """Repak a MS Office file."""
    with UnpackedZip(sourcename) as tempdir:
        basename, ext = osp.splitext(sourcename)
        path_media = osp.join(tempdir, OOXML_MEDIA[ext])

        # compress png media
        args = [UTIL_EXE.get('optipng', None)]
        if args[0] is not None:
            args.extend(('-o5', '-quiet', osp.join(path_media, "*.png")))
            subprocess.run(args)

        # compress jpg media
        if 'jpegtran' in UTIL_EXE:
            jlist = glob(osp.join(path_media, '*.jpeg'))
            jlist.extend(glob(osp.join(path_media, '*.JPEG')))
            jlist.extend(glob(osp.join(path_media, '*.jpg')))
            for jpegfile in jlist:
                optimize_jpg(jpegfile, jpegfile, extra_markers='none')
          
        repack_folder(tempdir, destname) # TODO: use zipfile if no 7z
        
 
def tar2zip(tarfilename, zipfilename=None):
    """Convert the given tarfile to a zipfile."""
    if zipfilename is None:
        zipfilename = osp.splitext(tarfilename)[0] + '.zip'

    fromtimestamp = datetime.datetime.fromtimestamp
    def timetuple(mtime):
        """convert tarfile mtime to zipfile time tuple"""
        return fromtimestamp(mtime).timetuple()[:6]

    with tarfile.open(tarfilename) as tf:
        with zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as zf:
            for mem in tf.getmembers():
                zipinf = zipfile.ZipInfo(mem.name, timetuple(mem.mtime))
                zf.writestr(zipinf, tf.extractfile(mem).read(),
                            zipfile.ZIP_DEFLATED)

    shutil.copystat(tarfilename, zipfilename)

#============================= MAIN ==========================================
def repack_files(filenames, preserve=True, keep=False, verbose=True, **kws):
    """Repack each of the given files"""
    tot1 = 0
    tot2 = 0
    sow = sys.stdout.write
    for sourcefile in glob(filenames):
        basename, ext = osp.splitext(sourcefile)
        if ext.lower() not in ACCEPTED_TYPES:
            continue # skip unsupported files
        size1 = os.stat(sourcefile).st_size
        if ext.lower() == '.tar':
            tar2zip(sourcefile)
            continue
        if ext.lower() in OPTIPNG_ALT_TYPE:
            args = [UTIL_EXE.get('optipng', None)]
            if args[0] is not None:
                args.extend(('-o5', '-preserve', sourcefile))
                subprocess.run(filenames)
            continue
            
        backup_source = basename + '_bak' + ext
        os.rename(sourcefile, backup_source)
        destfile = sourcefile
        
        ext = ext.lower()
        if ext in OOXML_MEDIA:
            repack_ooxml(backup_source, destfile)
        elif ext in ZIP_TYPE:
            repack_zip(backup_source, destfile)
        elif ext == '.png':
            optimize_png(backup_source, destfile)
        elif ext in JPG_TYPE:
            optimize_jpg(backup_source, destfile)
        elif ext == '.h5':
            h5repack(backup_source, destfile)
        
        size2 = os.stat(destfile).st_size
        if verbose:
            tot1 += size1
            tot2 += size2
            print_oneline_summary(sourcefile, size1, size2)
        
        if size1 <= size2: #src_is_smaller(backup_source, destfile):
            # restore original file if it is smaller
            os.remove(destfile)
            os.rename(backup_source, destfile)
            tot2 += size1 - size2
        elif preserve:
            shutil.copystat(backup_source, destfile)

        if not keep and osp.isfile(backup_source):
            os.remove(backup_source)

    if verbose:
        print_oneline_summary(sourcefile, tot1, tot2)


def parse_args():
    """Parse command-line arguments using argparse module"""
    parser = argparse.ArgumentParser(
        prog=osp.split(__file__)[1],
        usage="\r{} v{}\nusage: %(prog)s [options] srcfile ".format(
            osp.split(__file__)[1][:-3], __version__),
        formatter_class=argparse.RawTextHelpFormatter,
        description=__doc__,
    )
    parser.add_argument('srcfile', action='store',
                        help="source file, or list of source files")
    parser.add_argument('-v', '--version', action='version',
                        version="%(prog)s v{}".format(__version__),)
    parser.add_argument('-p', '--preserve',
                        dest='preserve', action='store_true', default=True,
                        help="preserve file attributes [default True]")
    parser.add_argument('-k', '--keep', '--backup',
                        dest='keep', action='store_true', default=False,
                        help="keep original file, appending _bak to filename")
    parser.add_argument('-q', '--quiet', dest='verbose', action='store_false',
                        help="don't print progress report")

    if len(sys.argv) == 1: # print help if no arguments
        parser.print_help()
        parser.exit(1)

    return parser.parse_args()

def main():
    args = parse_args()
    repack_files(args.srcfile, **vars(args))

if __name__ == '__main__':
    main()
