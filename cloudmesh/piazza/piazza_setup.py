import os, sys, shutil, getpass, ConfigParser
from cloudmesh.piazza.piazza_mongo import PiazzaMongo
import config

class PiazzaSetup:
    '''Setup directory for Piazza analysis. Run from commandline "piazza setup"
    '''  
    def needs_install(self):
        '''Check if piazza is installed
        Returns:
            (bool) -- whether or not piazza is installed
        '''
        if(not os.path.isfile(os.path.expanduser('~/piazza/piazza.cfg'))):
            print '"piazza.cfg" doesn\'t exist. Entering install.'
            return True
        else:
            return False
            
    def needs_setup(self):
        '''Check if piazza is setup
        Returns:
            (bool) -- whether or not piazza is setup
        '''
        m = PiazzaMongo()
        if(not m.collection_in_db('posts') or not m.collection_in_db('meta') or not m.collection_in_db('piazza_users')):
            setup = self.get_y_n('MongoDB is not setup for Piazza Miner. Run Setup now?')
            if(setup):
                return True
        return False  
            
    def install(self):
        '''Move necessary files to new folder
        '''
        install = self.get_y_n('Do you wish to install Piazza Miner to {folder}'.format(folder = os.path.expanduser('~/piazza')))
        if(install):
            self.move_files()
            self.modify_config()
            print 'Install complete.'
        else:
            sys.exit('Cannot continue without installation. Exiting program.')
    
    def setup(self):
        '''Setup piazza
        '''
        m = PiazzaMongo()
        m.setup_db()
        
        print 'Mongo setup complete.'
        print 'Setup complete.'
        
    def move_files(self):
        '''Move files from files/ folder in package to piazza folder
        '''
        print 'Copying include files.'
        
        try:
            includes = os.path.dirname(sys.modules[__name__].__file__) + '/includes'
            shutil.copyfile(includes + '/piazza.cfg', os.path.expanduser('~/piazza/piazza.cfg'))
        except OSError as e:
            sys.exit('Could not copy include files. Exiting program.')
        
    def modify_config(self):
        '''Create piazza.cfg file
        '''
        modify = self.get_y_n('Do you wish to modify "piazza.cfg"? NOTE: Information provided will be stored in the piazza.cfg file.')
                
        if(modify): 
            email = raw_input('[piazza] Enter your Piazza login email: ')
            password = getpass.getpass('[piazza] Enter your Piazza login password: ')
            nid = raw_input('[piazza] Enter the Piazza network/class ID (default is "ix39m27czn5uw"): ')
            
            nid = nid if nid else config.get('network', 'id')

            print 'Writing piazza.cfg'
            
            c = ConfigParser.SafeConfigParser()
            c.readfp(open(os.path.expanduser('~/piazza/piazza.cfg')))
            c.set('login', 'email', email)
            c.set('login', 'password', config.encrypt(password))
            c.set('network', 'id', nid)
            with open(os.path.expanduser('~/piazza/piazza.cfg'), 'wb') as f:
                c.write(f)
                
    def get_y_n(self, message):
        '''Prompt y/n message, return True or False
        Args:
            message (string) -- for raw_input
        Returns:
            (bool) -- user input
        '''      
        while(True):
            i = raw_input('[piazza] {message} (y/n) '.format(message = message))
            if(i == 'y'):
                return True
            elif(i == 'n'):
                return False

            

