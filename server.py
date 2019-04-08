import json
import os.path
import sys
import datetime
from werkzeug.utils import secure_filename
import imghdr
from flask import Flask, render_template, request, redirect
app = Flask(__name__)

class jsonmanager():
    users = {}
    PHOTOPATH = ""
    USERFILE = ""

    def __init__(self, PHOTOPATH, USERFILE):
        # Load user accounts, create if do not exist
        self.USERPATH = os.path.join(PHOTOPATH, USERFILE)
        if os.path.isfile(self.USERPATH):
            with open(self.USERPATH, "r") as f:
                self.users = json.load(f)

        else:
            with open(self.USERPATH, "w+") as f:
                json.dump(self.users, f)

        self.PHOTOPATH = PHOTOPATH
        self.USERFILE = USERFILE

    def save(self):
        with open(os.path.join(self.PHOTOPATH, self.USERPATH), "w") as f:
            json.dump(self.users, f)

    def reload(self):
        with open(self.USERPATH, "r") as f:
            self.users = json.load(f)



class usermanager(jsonmanager):
    def getusertoken(self, username):
        try:
            return self.users[username]["token"]
        except KeyError:
            return None


class photomanager():
    PHOTOPATH = ""
    cache = {}
    metaname = "meta.json"
    cacherecord = {}
    ALLOWED_EXTENSIONS = set([])

    def __init__(self, PHOTOPATH, cols, ALLOWED_EXTENSIONS, DATE_FORMAT):
        if not os.path.exists(PHOTOPATH):
            os.makedirs(PHOTOPATH)
        self.PHOTOPATH = PHOTOPATH
        self.ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
        self.DATE_FORMAT = DATE_FORMAT
        self.cols = cols

        self.reindex()

        
    def resetalbumrecord(self):
        self.cacherecord = {}
        for albumname, albumdata in self.cache.items():
            self.cacherecord[albumname] = [albumdata[col] for col in self.cols]


    # Index the currently stored albums
    def reindex(self):
        self.cache = {}

        for albumname in os.listdir(self.PHOTOPATH):
            fullpath = os.path.join(self.PHOTOPATH, albumname, self.metaname)

            if os.path.isfile(fullpath):
                with open(fullpath, 'r') as f:
                    self.cache[albumname] = json.load(f)["meta"]

        self.resetalbumrecord()


    def setalbumdata(self, albumname, albumdata):
        cache[albumname] = albumdata
        
        with open(os.path.join(self.PHOTOPATH, albumname, self.metaname), 'r+') as f:
            album = json.load(f)
            album["meta"] = albumdata
            json.dump(album, f)

        record = [albumdata[col] for col in self.cols]
        self.cacherecord[albumname] = record


    def getalbumdata(self, albumname):
        try:
            return self.cache[albumname]
        except KeyError:
            return None

    def sortby(self, d, sortby, reverse):
        cacherecord = list(d.items())
        cacherecord.sort(key = lambda x: x[1][self.cols.index(sortby)])
        if reverse:
            return cacherecord[::-1]
        return cacherecord


    def sortalbumrecord(self, sortby, reverse=False):
        return self.sortby(self.cacherecord, sortby, reverse)


    def getalbumphotodata(self, albumname):
        with open(os.path.join(self.PHOTOPATH, albumname, self.metaname), 'r') as f:
            photodata = json.load(f)["photos"]

        photorecords = {}
        for photoname, photodata in photodata.items():
            
            photorecords[photoname] = [photodata[col] for col in self.cols]

        return photorecords

    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS


    def createphoto(self, photo, albumname, photoname, displayname, creator, date):
        # Test for correct file extension
        if not self.allowed_file(photoname):
            return None

        # Test that the file is an image
        #photo.save("./tmpimage")
        #if imghdr.what("./tmpimage") == None:
        #    os.remove("./tmpimage")
        #    return None
        
        # Save the photo
        #os.rename("./tmpimage", os.path.join(self.PHOTOPATH, albumname, photoname))
        photo.save(os.path.join(self.PHOTOPATH, albumname, photoname))

        # Update the album metadata
        with open(os.path.join(self.PHOTOPATH, albumname, self.metaname), 'r') as f:
            metadata = json.load(f)

        metadata["photos"][photoname] = {}
        metadata["photos"][photoname]["Display Name"] = displayname
        metadata["photos"][photoname]["Creator"] = creator
        metadata["photos"][photoname]["Date"] = date
        metadata["photos"][photoname]["Last Modified"] = datetime.datetime.now().strftime(self.DATE_FORMAT)
        with open(os.path.join(self.PHOTOPATH, albumname, self.metaname), 'w') as f:
            json.dump(metadata, f)
    
        return True




PHOTOPATH = "./static/photos/"
USERFILE = "users.json"
PHOTOCOLS = ["Display Name", "Creator", "Date", "Last Modified"]
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
DATE_FORMAT = "%Y-%m-%d"

userman = usermanager('', USERFILE)
photoman = photomanager(PHOTOPATH, PHOTOCOLS, ALLOWED_EXTENSIONS, DATE_FORMAT)


def authenticate(request):
    try:
        token = request.args.get('token')
        name = request.args.get('name')
    except KeyError:
        return None

    if token == None or name == None or userman.getusertoken(name) != token:
        return None

    return name


@app.route("/", methods=['GET'])
def index():
    name = authenticate(request)
    if name == None:
        return render_template("invalid_token.html", token="")

    table = photoman.sortalbumrecord("Date", reverse=True)
    return render_template("index.html", name=name, cols=PHOTOCOLS, table=table)


@app.route("/albums/<albumname>", methods=['GET', 'POST'])
def albumpage(albumname):
    # Token authentication
    name = authenticate(request)
    if name == None:
        return render_template("invalid_token.html", token="")

    # Display the album page
    if request.method == 'GET':
        if not albumname in photoman.cache.keys():
            return "404 - album not found"
        
        metadata = zip(PHOTOCOLS, photoman.cacherecord[albumname])
        photodata = photoman.sortby(photoman.getalbumphotodata(albumname), "Date", reverse=True)
        return render_template("album.html", albumname=albumname, metadata=metadata, cols=PHOTOCOLS, photodata=photodata)

    # Allow file uploads
    if request.method == 'POST':
        for displayname, f in request.files.items():
            # Sanitise filename and save
            ret = photoman.createphoto(f, albumname, secure_filename(f.filename), f.filename, name, "")
            if ret == None:
                return "Upload unsuccessful"

        return "Upload successful"




