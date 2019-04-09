# gremlins-photobot
gremlins-photobot is a free as in freedom server systen for collating photos with friends, built with flask.
Dedicated to my dad for his 51st birthday.


## Getting Started
### Prerequisites
Python module dependencies:
> flask
> datetime
> werkzeug
> exif
> json
> configparser
> urllib


### Setup
1. Clone the repository
> $ git clone https://github.com/EdwardSalkield/gremlins-photobot.git
> $ cd gremlins-photobot

2. Configure the server
  a. Setting up the config file
_server.conf_ is the default configuration file. Within it, you can configure attributes such as the server hostname, port to bind to, and location of the photos directory (see next section).

To location of the config file can be configured with the environment variable _GREMLINS\_PHOTOBOT\_SETTINGS:
> export GREMLINS\_PHOTOBOT\_SETTINGS=/path/to/your/server.conf

  b. Configuration
gremlins-photobot

Config Option | Meaning
------------- | -------
SERVER_NAME | Hostname and port to serve on. 0.0.0.0 for all interfaces.
DEBUG | True puts the server into [flask debug mode] (http://flask.pocoo.org/docs/1.0/quickstart/#debug-mode).
STATIC_LOCATION | The location of the directory to serve static files from.
PHOTO_LOCATION | The subdirectory of STATIC_LOCATION to store albums.
USER_FILE_LOCATION | The name of the user config file.
ALLOWED_EXTENSIONS | The allowed filetypes for upload.
DATE_FORMAT | The date format to be displayed.
URL_BASE_PATH | The base path for the url of the server.

For more details, see the [flask builtin configuration values](http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values).


3. Set up user accounts.
User accounts are configured by USER_FILE_LOCATION. This file contains the username, the unique login token, and a boolean flag for admin access, per user.
You should add at least one user to this file.

Example users.json:
>{
>        "edd": {
>                "token": "test",
>                "admin": true
>        }
>}


4. Launch the server
Recommended: deploy the flask server as per [these instructions](http://flask.pocoo.org/docs/0.12/deploying/)
Alternative: Run Flask's built-in server:
> python3 server.py


5. Connecting to the server
Users login to the server with url-encoded tokens. In a web browser, navigate to http://yourdomain.tld:port/login?name=username&token=yourtoken.


6. Administrator access
Users with the admin flag set to true in USER_FILE_LOCATION are permitted to access the /admin url.
From here, the server cache can be reset.


## Built with
* [flask](https://github.com/pallets/flask)
* [jinja2](https://github.com/pallets/jinja)


## Authors
* **Edd Salkield**


## License
This project is licensed under GPLv3 - see the COPYING file for details.
