import json
import os.path
import os
import sys
import datetime
from werkzeug.utils import secure_filename
import urllib.parse
from exif import Image
from flask import Flask, render_template, request, redirect, session, url_for
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
    ALBUMCOLS = []
    PHOTOCOLS = []

    def __init__(self, PHOTOPATH, PHOTOCOLS, ALBUMCOLS, ALLOWED_EXTENSIONS, DATE_FORMAT):
        if not os.path.exists(PHOTOPATH):
            os.makedirs(PHOTOPATH)
        self.PHOTOPATH = PHOTOPATH
        self.ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
        self.DATE_FORMAT = DATE_FORMAT
        self.PHOTOCOLS = PHOTOCOLS
        self.ALBUMCOLS = ALBUMCOLS

        self.reindex()

        
    def resetalbumrecord(self):
        self.cacherecord = {}
        for albumname, albumdata in self.cache.items():
            try:
                self.cacherecord[albumname] = [albumdata[col] for col in self.ALBUMCOLS]
            except KeyError:
                continue


    # Index the currently stored albums
    def reindex(self, album=None):

        if album == None:
            self.cache = {}
            albums = os.listdir(self.PHOTOPATH)
        else:
            albums = [album]

        for albumname in albums:
            fullpath = os.path.join(self.PHOTOPATH, albumname, self.metaname)
            ALBUMCOLS = []
            PHOTOCOLS = []

            if os.path.isfile(fullpath):
                with open(fullpath, 'r') as f:
                    self.cache[albumname] = json.load(f)["meta"]

        self.resetalbumrecord()


    def setalbumdata(self, albumname, albumdata):
        self.cache[albumname] = albumdata
        
        metapath = os.path.join(self.PHOTOPATH, albumname, self.metaname)
        if os.path.exists(metapath):
            with open(metapath, 'r+') as f:
                album = json.load(f)
                album["meta"] = albumdata
                json.dump(album, f)

        else:
            with open(metapath, 'w') as f:
                album = {"meta": {}, "photos": {}}
                album["meta"] = albumdata
                json.dump(album, f)


        record = [albumdata[col] for col in self.ALBUMCOLS]
        self.cacherecord[albumname] = record


    def getalbumdata(self, albumname):
        try:
            return self.cache[albumname]
        except KeyError:
            return None

    def sortby(self, d, sortby, reverse, cols):
        cacherecord = list(d.items())
        cacherecord.sort(key = lambda x: x[1][cols.index(sortby)])
        if reverse:
            return cacherecord[::-1]
        return cacherecord


    def sortalbumrecord(self, sortby, reverse=False):
        return self.sortby(self.cacherecord, sortby, reverse, self.ALBUMCOLS)


    def getalbumphotodata(self, albumname):
        with open(os.path.join(self.PHOTOPATH, albumname, self.metaname), 'r') as f:
            photodata = json.load(f)["photos"]

        photorecords = {}
        for photoname, photodata in photodata.items():
            
            photorecords[photoname] = [photodata[col] for col in self.PHOTOCOLS]

        return photorecords

    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    # Create new photoalbum
    def createalbum(self, albumname, displayname, creator, date, restricted):
        albumpath = os.path.join(self.PHOTOPATH, albumname)
        
        # Create album directory
        if os.path.exists(albumpath):
            raise ValueError("Album of this name already exists!")
        
        os.makedirs(albumpath)

        # Create metadata
        metadata = {}
        metadata["Display Name"] = displayname
        metadata["Creator"] = creator
        metadata["Date"] = date
        metadata["Number of Photos"] = 0
        metadata["Last Modified"] = "Never"
        metadata["Restricted"] = displayname

        self.setalbumdata(albumname, metadata)



    def createphoto(self, photo, albumname, photoname, displayname, creator):
        # Test for correct file extension
        if not self.allowed_file(photoname):
            return None

        photopath = os.path.join(self.PHOTOPATH, albumname, photoname)
        # Test if the file exists
        if os.path.exists(photopath):
            return


        photo.save(photopath)

        # Get the photo timestamp
        with open(photopath, 'rb') as image_file:
            try:
                image = Image(image_file)
                date = image.datetime.replace(':', '-')
            except Exception:
                date = ""


        # Update the album metadata
        albumpath = os.path.join(self.PHOTOPATH, albumname, self.metaname)
        with open(albumpath, 'r') as f:
            metadata = json.load(f)

        metadata["photos"][photoname] = {}
        metadata["photos"][photoname]["Display Name"] = displayname
        metadata["photos"][photoname]["Creator"] = creator
        metadata["photos"][photoname]["Date"] = date
        metadata["photos"][photoname]["Last Modified"] = datetime.datetime.now().strftime(self.DATE_FORMAT)
        metadata["meta"]["Number of Photos"] += 1
        metadata["meta"]["Last Modified"] = datetime.datetime.now().strftime(self.DATE_FORMAT)


        with open(albumpath, 'w') as f:
            json.dump(metadata, f)

        self.reindex(albumname)




PHOTOPATH = "./static/photos/"
USERFILE = "users.json"
ALBUMCOLS = ["Display Name", "Creator", "Date", "Number of Photos", "Last Modified", "Restricted"]
PHOTOCOLS = ["Display Name", "Creator", "Date", "Last Modified"]
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
DATE_FORMAT = "%Y-%m-%d %H-%M-%S"

userman = usermanager('', USERFILE)
photoman = photomanager(PHOTOPATH, PHOTOCOLS, ALBUMCOLS, ALLOWED_EXTENSIONS, DATE_FORMAT)


def authenticate(request):
    try:
        token = request.args.get('token')
        name = request.args.get('name')
    except KeyError:
        return None

    if token == None or name == None or userman.getusertoken(name) != token:
        return None

    return name

def is_authenticated(session):
    try:
        return session['auth'] == True and session['name'] != None
    except KeyError:
        return False


@app.route("/login", methods=['GET', 'POST'])
def login():
    name = authenticate(request)
    if name == None:
        return render_template("invalid_token.html", token="")
    session['name'] = name
    session['auth'] = True
    return redirect(url_for('index'))
		

@app.route("/", methods=['GET', 'POST'])
def index():
    if not is_authenticated(session):
        return render_template("invalid_token.html", token="")

    name = session['name']

    if request.method == 'GET':
        table = photoman.sortalbumrecord("Date", reverse=True)
        return render_template("index.html", name=name, cols=ALBUMCOLS, table=table)

    elif request.method == 'POST':
        #try:
        displayname = request.form['name']
        date = request.form['date']
        try:
            request.form['restricted']
            restricted = True
        except KeyError:
            restricted = False
        #except KeyError:
        #    return "Malformatted form."

        albumname = urllib.parse.quote(displayname.lower().replace(" ", "_"))

        try:
            photoman.createalbum(albumname, displayname, name, date, restricted)
        except ValueError as e:
            return str(e)

        return redirect(url_for('albumpage', albumname=albumname))


@app.route("/logout")
def logout():
    session.pop('name', None)
    session.pop('auth', None)
    return "Logged out successfully."

@app.route("/albums/<albumname>", methods=['GET', 'POST'])
def albumpage(albumname):
    if not is_authenticated(session):
        return render_template("invalid_token.html", token="")

    name = session['name']

    # Display the album page
    if request.method == 'GET':
        if not albumname in photoman.cache.keys():
            return "404 - album not found"
        
        metadata = zip(ALBUMCOLS, photoman.cacherecord[albumname])
        photodata = photoman.sortby(photoman.getalbumphotodata(albumname), "Date", True, PHOTOCOLS)
        return render_template("album.html", albumname=albumname, metadata=metadata, cols=PHOTOCOLS, photodata=photodata)

    # Allow file uploads
    if request.method == 'POST':
        photoname = request.form["photoname"]

        files = request.files.getlist("file")

        for i, f in enumerate(files):
            if photoname == "":
                pname = f.filename
            else:
                pname = photoname
                if i > 0:
                    pname = pname + '_' + str(i)

            # Sanitise filename and save
            try:
                photoman.createphoto(f, albumname, secure_filename(f.filename), pname, name)
            except ValueError as e:
                return str(e)

        return redirect(url_for('albumpage', albumname=albumname))

# 404 page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

app.secret_key = os.urandom(24)

