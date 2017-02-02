import time, sys
import pymongo
import config

class PiazzaMongo:
    '''MongoDB interface for Piazza Miner
    '''
    def __init__(self):
        port = config.get('mongo', 'port')
        port = int(port) if port else 27017
    
        # ensure mongo is running
        try:
            client = pymongo.MongoClient(port = port, serverSelectionTimeoutMS = 1)
            client.server_info()
            client.close()
        except pymongo.errors.ServerSelectionTimeoutError as err:
            sys.exit('Could not connect to MongoDB: {err}'.format(err = err))
        
        self.nid = config.get('network', 'id')
        self.client = pymongo.MongoClient(port = port)
        self.db = self.client[self.get_db_name()]
        
    def setup_db(self):
        '''Setup databse: user collection
        '''
        print 'Setting up MongoDB database.'
        
        print 'Creating "meta", "piazza_users" and "posts" collections.'
        self.db['meta'].insert({'updated':0})
        self.db.piazza_users.create_index('id', unique = True)
        self.db.posts.create_index('id', unique = True)
        
    def get_db_name(self):
        '''Get database name, based on network id
        '''
        return 'piazza_' + self.nid
        
    def drop(self, collection):
        '''Drop folder (collection)
        Args:
            collection (string) -- name of collection to drop
        '''
        return self.db[collection].drop()
        
    def update_one(self, collection, query, update):
        '''Update single document
        Args:
            collection (string) -- collection document is in
            query (dict) -- query
            update (dict) -- update query with $set
        '''
        self.db[collection].update_one(query, update)
        
    def check_update(self): 
        '''Check whether or not file should be updated
        Args:
            folder (string) -- folder that should be checked
        Returns:
            (bool) -- whether or not file should be updated
        '''        
        update_interval = config.get('network', 'update')
        
        if(update_interval == 'never'):
            return False
        elif(update_interval == 'always'):
            return True
        else:            
            updated_on = self.find_one('meta', {}, {'updated': 1})['updated']
            
            if(updated_on == 0):
                print 'Database must be updated before analysis. Running update now.'
                return True
            
            print 'Last updated on: {date}'.format(date = time.strftime("%a, %d %b %Y %H:%M", time.localtime(updated_on)))
            
            times = {
                'hour': 60 * 60,
                'day': 60 * 60 * 24,
                'week': 60 * 60 * 24 * 7
            }
            
            update_time = time.time() - times[update_interval]
            
            if(update_time > updated_on):
                while(True):
                    update = raw_input('Database is out of date. Update now? (y/n) ')
                    if(update == 'y'):
                        return True
                    elif(update == 'n'):
                        return False
            else:
                return False

    def insert(self, collection, item):
        '''Insert posts into collection (named after folder)
        Args:
            folder (string) -- name of folder/collection
            item (dict) -- item to insert
        '''
        try:
            self.db[collection].insert_one(item)
        except pymongo.errors.DuplicateKeyError:
            pass
        
    def insert_many(self, collection, items):
        '''Insert posts into collection (named after folder)
        Args:
            folder (string) -- name of folder/collection
            item (iterable) -- items to insert
        '''
        self.db[collection].insert_many(items)
        
    def collection_in_db(self, collection):
        '''Determine whether or not folder is in database
        Args:
            folder (string) -- name of folder
        Return:
            (bool) -- whether or not folder exists
        '''
        return collection in self.db.collection_names()
        
    def find(self, collection, query = {}, fields = {}, sort = None):
        '''Return fields from folder
        Args:
            folder (string) -- folder name
            query (dict) -- query
            fields (dict) -- fields to return
        Returns:
            (pymongo Cursor)
        '''
        if(fields):
            result = self.db[collection].find(query, fields)
        else:
            result = self.db[collection].find(query)
            
        if(sort == 'ascending'):
            result.sort('name', pymongo.ASCENDING)
            
        return result
        
    def find_one(self, collection, query = {}, fields = {}):
        '''Return field from folder
        Args:
            folder (string) -- folder name
            query (dict) -- query
            fields (dict) -- fields to return
        Returns:
            (dict) -- document
        '''
        if(fields):
            return self.db[collection].find_one(query, fields)
        else:
            return self.db[collection].find_one(query)          
            
    def replace_one(self, collection, query, replacement):
        '''Replace one item
        Args:
            folder (string) -- folder name
            query (dict) -- filter for replacement
            replacement (dict) -- item to replace old one with
        Returns:
            (pymongo.results.UpdateResult)
        '''
    
        return self.db[collection].replace_one(query, replacement) 
            
    def search_for_user(self, name):
        '''Get students whose names contain 'name'
        Args:
            name (string) -- name to search for
        Returns:
            (list) -- results
        '''
        result = []
        for user in self.db.piazza_users.find({}, {'_id': 0}).sort('name', pymongo.ASCENDING):
            if(name.lower() in user['name'].lower()):
                result.append(user)
                
        return result
