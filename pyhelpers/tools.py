import urllib.request
import os
import config as cfg
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


def downloadFileWithProgress(url, barlength=20, incrementPercentage = 10, incrementKB = 0, printOutput = True, folder = './', overwrite = True, localfilename='.'):
    """
    Download a file from an URL, and show the download progress.
    :param url: the source URL
    :param barlength: the length of the progress bar (default 20). Set to 0 to disable progress bar
    :param incrementPercentage: update progress every X percent (default 10). This is ignored when incrementPercentage>0 is used. If both incrementPercentage and incrementKB are 0, no propgress is displayed
    :param incrementKB: update display every X KB (default 0, which means it is disabled)
    :param printOutput: set to False if you wish no output (default True)
    :param folder: name of folder with "/" at the end (default './'
    :param overwrite: overwrite existing files (default True)
    :param localfilename: the name of the local file (default is the name of the remote file)
    :return:
    """
    if (barlength > 0):
        barlengthDivisor = 100 / barlength

    # check local file
    if localfilename is '.':
        file_name = folder + url.split('/')[-1]
    else:
        file_name = folder + localfilename
    if os.path.exists(file_name) and not overwrite:
        if printOutput:
            print('Skipping ' + file_name)
        return

    # get remote file info
    u = urllib.request.urlopen(url)
    meta = u.info()
    length = meta['Content-Length']
    if meta['Content-Length'] is not None:
        file_size = int(meta['Content-Length'])
    else:
        # disable display if cannot size
        file_size = -1
        barlength = 0
        incrementKB = 0
        incrementPercentage = 0
    if file_size is 0:
        raise BaseException('File size is 0')

    if printOutput:
        print('Downloading: {:s}   {:1.0f} KB'.format(url, file_size/1024))

    # set KB increments
    if (incrementKB > 0):
        incrementPercentage = 100 * incrementKB / (file_size / 1024)


    # transfer file
    f = open(file_name, 'wb')
    file_size_dl = 0
    block_sz = 8192
    nextIncrement = 0
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)

        # output progress
        if printOutput and (incrementPercentage > 0 or incrementKB > 0):
            currentPercentage = file_size_dl * 100. / file_size
            status ='{:10.0f}KB {:05.2f}%  '.format(file_size_dl / 1024, currentPercentage)
            if barlength>0:
                status = status + '|'+ '#' * int(currentPercentage / barlengthDivisor) + ' ' * int(barlength - currentPercentage / barlengthDivisor) + '|'
            if currentPercentage >= nextIncrement:
                print (status)
                nextIncrement = nextIncrement + incrementPercentage
    f.close()
    return

##
def normalizeDBLPkey(dblpkey):
    """
    tTakes a raw dblp key and converts replaces / with _ (so that you can use it for filenames etc)
    :param dblpkey: raw dblp key as extracted from DBLP XML
    :return: normalized key
    """
    return dblpkey.replace("/", "_")

##
def create_all_folders():
    """
    Creates all required folders
    """
    os.makedirs(cfg.folder_dblp_xml, exist_ok=True)
    os.makedirs(cfg.folder_content_xml, exist_ok=True)
    os.makedirs(cfg.folder_pdf, exist_ok=True)
    os.makedirs(cfg.folder_log, exist_ok=True)

##
def setup_logging():
    # setup logging
    import logging
    create_all_folders()
    logging.basicConfig(format='%(asctime)s %(message)s', filename=cfg.folder_log+'last_log.log',
                        level=logging.DEBUG, filemode='w')
    logging.debug("Start XML Parsing")
    logging.getLogger().addHandler(logging.StreamHandler())


def connect_to_mongo():
    """
    Returns a db connection to the mongo instance
    :return:
    """
    try:
        client = MongoClient()
        db = client.pub
        db.downloads.find_one({'_id': 'test'})
        return db
    except ServerSelectionTimeoutError as e:
        raise Exception("Local MongoDB instance cannot be accessed.") from e
# downloadFileWithProgress('http://aclweb.org/anthology/Y/Y06/Y06-1007.pdf', incrementKB=10 * 1024, overwrite=True)