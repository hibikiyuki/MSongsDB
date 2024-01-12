import os
import sys
import hdf5_getters
import numpy as np

def die_with_usage():
    """ HELP MENU """
    print('display_song.py')
    print('T. Bertin-Mahieux (2010) tb2332@columbia.edu')
    print('to quickly display all we know about a song')
    print('usage:')
    print('   python display_song.py [FLAGS] <HDF5 file> <OPT: song idx> <OPT: getter>')
    print('example:')
    print('   python display_song.py mysong.h5 0 danceability')
    print('INPUTS')
    print('   <HDF5 file>  - any song / aggregate /summary file')
    print('   <song idx>   - if file contains many songs, specify one')
    print('                  starting at 0 (OPTIONAL)')
    print('   <getter>     - if you want only one field, you can specify it')
    print('                  e.g. "get_artist_name" or "artist_name" (OPTIONAL)')
    print('FLAGS')
    print('   -summary     - if you use a file that does not have all fields,')
    print('                  use this flag. If not, you might get an error!')
    print('                  Specifically designed to display summary files')
    sys.exit(0)

if __name__ == '__main__':
    """ MAIN """

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()

    # flags
    summary = False
    while True:
        if len(sys.argv) > 1 and sys.argv[1] == '-summary':
            summary = True
            sys.argv.pop(1)
        else:
            break

    # get params
    hdf5path = sys.argv[1]
    songidx = 0
    if len(sys.argv) > 2:
        songidx = int(sys.argv[2])
    onegetter = ''
    if len(sys.argv) > 3:
        onegetter = sys.argv[3]

    # sanity check
    if not os.path.isfile(hdf5path):
        print('ERROR: file', hdf5path, 'does not exist.')
        sys.exit(0)
    h5 = hdf5_getters.open_h5_file_read(hdf5path)
    numSongs = hdf5_getters.get_num_songs(h5)
    if songidx >= numSongs:
        print('ERROR: file contains only', numSongs)
        h5.close()
        sys.exit(0)

    # get all getters
    getters = [x for x in dir(hdf5_getters) if x.startswith('get_')]
    getters.remove("get_num_songs")  # special case
    if onegetter in ['num_songs', 'get_num_songs']:
        getters = []
    elif onegetter != '':
        if not onegetter.startswith('get_'):
            onegetter = 'get_' + onegetter
        if onegetter not in getters:
            print('ERROR: getter requested:', onegetter, 'does not exist.')
            h5.close()
            sys.exit(0)
        getters = [onegetter]
    getters.sort()

    # print them
    for getter in getters:
        try:
            res = getattr(hdf5_getters, getter)(h5, songidx)
        except AttributeError as e:
            if summary:
                continue
            else:
                print(e)
                print('Forgot -summary flag? Specified wrong getter?')
                continue
        if isinstance(res, np.ndarray):
            print(getter[4:] + ": shape =", res.shape)
        else:
            print(getter[4:] + ":", res)

    # done
    print('DONE, showed song', songidx, '/', numSongs - 1, 'in file:', hdf5path)
    h5.close()
