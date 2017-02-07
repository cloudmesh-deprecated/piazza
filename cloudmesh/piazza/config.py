import base64, ConfigParser, os

def get(section, name):
    config = ConfigParser.SafeConfigParser()
    config.readfp(open(os.path.expanduser('~/piazza/piazza.cfg')))
    return config.get(section, name)
    
def encrypt(string):
    return base64.b64encode(string)

def decrypt(string):
    return base64.b64decode(string)
    
def change(section, item, value):
    config = ConfigParser.SafeConfigParser()
    config.readfp(open(os.path.expanduser('~/piazza/piazza.cfg')))
    config.set(section, item, value)
    
    with open(os.path.expanduser('~/piazza/piazza.cfg'), 'wb') as f:
        config.write(f)
