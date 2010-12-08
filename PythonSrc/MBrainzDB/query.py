"""
Thierry Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu

This code query the musicbrainz database to get some information
like musicbrainz id and release years.
The databased in installed locally.

This is part of the Million Song Dataset project from
LabROSA (Columbia University) and The Echo Nest.


Copyright 2010, Thierry Bertin-Mahieux

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import pg
import glob
import numpy as np

USER='gordon'
PASSWD='gordon'


def connect_mbdb():
    """
    Simple connection to the musicbrainz database, returns a pgobject
    Return None if there is a problem
    """
    try:
        connect = pg.connect('musicbrainz_db','localhost',-1,None,None,
                             USER,PASSWD)
    except TypeError, e:
        print 'CONNECT_MBDB: type error, should not happen:',e
        return None
    except SyntaxError, e:
        print 'CONNECT_MBDB: syntax error, should not happen:',e
        return None
    except pg.InternalError, e:
        print 'CONNECT_MBDB, internal error:', e
        return None
    # check for levenshtein function
    q = "SELECT levenshtein('allo','allo2')"
    try:
        res = connect.query(q)
    except pg.ProgrammingError:
        print 'we need levenshtein (contrib) added to the database:'
        print 'psql -d musicbrainz_db -f /usr/share/postgresql/8.4/contrib/fuzzystrmatch.sq'
        connect.close()
        return None
    # done
    return connect


def get_aid_from_artist_mbid(connect,artist_mbid):
    """
    Get internal id for an artist from his musicbrainz id
    
    """
    res = connect.query("SELECT * FROM artist WHERE gid='"+artist_mbid+"'")
    if len(res.dictresult()) == 0:
        return None
    return res.dictresult()[0]['id']

def closest_song_by_name_and_aid(connect,artistid,title):
    """
    Return the closest song according to Levenshtein difference with a
    given id and title. All ' are replaced by spaces in the tile.
    Artistid is an integer, e.g. a musicbrainz internal ID.
    If no song is found, return None
    """
    q = "SELECT * FROM track WHERE artist="+str(artistid)
    q += " ORDER BY levenshtein(name,'"+title.replace("'"," ")+"') LIMIT 1"
    res = connect.query(q)
    if len(res.dictresult())>0:
        return res.dictresult()[0]
    return None


def track_durations_match(dur_target,dur_cand,threshold=.03):
    """
    Receives durations in same unit (seconds?), check if they are within
    the threshold. By default, threshold = 0.03, meaning 3% difference
    is tolerated.
    Return True if durations are close enough, False otherwise
    """
    if np.abs(dur_target-dur_cand * 1. / dur_target) < threshold:
        return True
    return False


def debug_from_song_file(connect,h5path):
    """
    Slow debugging function that takes a h5 file, reads the info,
    check the match with musicbrainz db, prints out the result.
    Only prints when we dont get exact match!
    """
    import hdf5_utils as HDF5
    from hdf5_getters import *
    h5 = HDF5.open_h5_file_read(h5path)
    title = get_title(h5)
    artist = get_artist_name(h5)
    ambid = get_artist_mbid(h5)
    if ambid == '':
        print '***************************************************'
        print 'artist:',artist,'song:',title
        print 'NO ARTIST MUSICBRAINZ ID'
        h5.close()
        return
    aid = get_aid_from_artist_mbid(connect,ambid)
    song = closest_song_by_name_and_aid(connect,aid,title)
    if (song['name'] != title):
        print '***************************************************'
        print 'artist:',artist,'song:',title
        print 'closest song:',song['name']
    h5.close()


def die_with_usage():
    """ HELP MENU """
    print 'This contains library functions to query the musicbrainz database'
    print 'For debugging:'
    print '    python query.py -go'
    print 'or'
    print '    python query.py -hdf5 <list of songs>'
    print '    python query.py -hdf5 millionsong/A/A/*/*.h5'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()

    # DEBUGGING

    if sys.argv[1] == '-hdf5':
        sys.path.append( os.path.abspath('..') )
        connect = connect_mbdb()
        paths = sys.argv[2:]
        for p in paths:
            debug_from_song_file(connect,p)
        connect.close()
        sys.exit(0)

    # connect
    connect = connect_mbdb()
    if connect is None:
        print 'could not connect to the database'
        sys.exit(0)

    # check all tables
    res = connect.query('select * from pg_tables')
    tablenames = map(lambda x: x['tablename'],res.dictresult())
    tablenames = np.sort(tablenames)
    print 'table names:',tablenames

    # get first and random artist
    res = connect.query('SELECT * FROM artist LIMIT 1')
    print 'first artist:',res.dictresult()
    res = connect.query('SELECT * FROM artist ORDER BY random() LIMIT 1')
    print 'random artist:',res.dictresult()

    # get Radiohead by artist id
    radiohead_mbid='a74b1b7f-71a5-4011-9441-d0b5e4122711'
    res = connect.query("SELECT * FROM artist WHERE gid='"+radiohead_mbid+"'")
    print 'Radiohead:',res.dictresult()
    if res.ntuples() > 1:
        print 'MORE THAN ONE RADIOHEAD????'
    print '***********************************************************'

    # get all albums from Radiohead
    
    # get all tracks from Radiohead
    artistid = res.dictresult()[0]['id']
    res = connect.query("SELECT * FROM track WHERE artist="+str(artistid))
    print 'we found',res.ntuples(),'tracks for Radiohead'
    alltracks = res.dictresult() # make sure the order doesn't change
    tracknames = map(lambda x: x['name'],alltracks)
    trackyears = map(lambda x: x['year'],alltracks)
    trackdurs = map(lambda x: x['length'],alltracks)
    trackgids = map(lambda x: x['gid'],alltracks)

    # get the track with the closest name
    target='No Surprises2'
    q = "SELECT * FROM track WHERE artist="+str(artistid)
    q += " ORDER BY levenshtein(name,'"+target.replace("'"," ")+"') LIMIT 1"
    res = connect.query(q)
    print 'closest track from Radiohead with name:',target
    print res.dictresult()[0]
    
    # close connect
    connect.close()