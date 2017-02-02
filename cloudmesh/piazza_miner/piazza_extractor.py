import getpass, json, sys, os, time
import requests
import grequests

from piazza_mongo import PiazzaMongo
import config

class PiazzaExtractor:
    '''Piazza API interface for Piazza Miner
    '''
    api_url = 'https://piazza.com/logic/api'
    
    def __init__(self):
        '''Get config, login, and set class_id
        '''
        self.email, self.password, self.class_id, update = self.get_piazza_info()
        
    def get_piazza_info(self):
        '''Open config file (default piazza.cfg)
        Returns:
            email (string), password (string), class_id (string)
        '''
        email = config.get('login', 'email')
        password = config.decrypt(config.get('login', 'password'))
        class_id = config.get('network', 'id')
        update = config.get('network', 'update')
        
        return email, password, class_id, update
        
    def login(self):
        '''Login to Piazza and get cookie
        Args:
            email (string) -- login email
            password (string) -- login password
        '''
        # get username and password
        email = self.email if self.email else raw_input('Enter login email: ')
        password = self.password if self.password else getpass.getpass('Enter your password')

        # login request to get cookie
        print 'Logging in as {email}.'.format(email = email)
        login_data = json.dumps({
            'method': 'user.login',
            'params': {
                'email': email,
                'pass': password
        }})
        r = requests.post(self.api_url, data=login_data)
        
        # login error
        if(r.json()['error']):
            sys.exit('Error logging in: {msg}. Please check your piazza.cfg file or run "piazza setup" in the command line.'.format(msg = r.json()['error']))
        
        self.login_cookie = r.cookies
        
    def get_folder_list(self):
        '''Get list of folders for class (network)
        Returns:
            (list) -- folder names
        '''
        post_data = json.dumps({
            'method': 'user.status',
            'params': {
                'nid': self.class_id
            }
        })
        
        r = requests.post(self.api_url, data=post_data, cookies=self.login_cookie)
        networks = r.json()['result']['networks']
        
        # find correct network (class)
        for network in networks:
            if(network['id'] == self.class_id):
                return network['folders']
                
    def get_all_posts(self):
        '''Get all posts from folder, updating if necessary
            Args:
                folder (string) -- folder to get posts from
            Returns:
                (dict) -- of posts
        '''
        print 'Getting posts.'
            
        data = json.dumps({
            'method': 'network.get_my_feed',
            'params': {
                'nid': self.class_id
            }
        })
        r = requests.post(self.api_url, data=data, cookies = self.login_cookie)
        folder_feed = json.loads(r.content)['result']['feed']
        
        m = PiazzaMongo()
        m.update_one('meta', {}, {'$set': {'updated': time.time()}})
        
        class Progress:
            '''Class for tracking download progress
            '''
            def __init__(self, total):
                self.count = 0
                self.total = total

            def update(self, r, **kwargs):
                self.count += 1
                sys.stdout.write('\r')
                sys.stdout.write(str(self.count) + '/' + str(self.total))
                sys.stdout.flush()
                if(self.count == self.total): print
                    
                return r
                
        prog = Progress(len(folder_feed))       
        reqs = []
        for post in folder_feed:
            data = json.dumps({'method': 'content.get', 'params': {'cid': post['id'], 'nid': self.class_id}})
            req = grequests.post(self.api_url, data = data, callback = prog.update, cookies = self.login_cookie)
            reqs.append(req)
            
        responses = grequests.map(reqs)
               
        posts = []
        for r in responses:
            r = r.json()['result']
            
            post = {}
            post['created'] = r['created']
            post['type'] = r['type']
            post['tags'] = r['tags']
            post['folders'] = r['folders']
            post['id'] = r['id']
            post['cid'] = r['nr']
            post['num_favorites'] = r['num_favorites']
            post['good_tags'] = len(r['tag_good'])
            post['answered'] = r['no_answer'] == 0 if 'no_answer' in r else True
            
            original_post = r['history'][-1]
            recent_post = r['history'][0]
            
            post['author_id'] = original_post['uid'] if 'uid' in original_post else None
            post['last_edited'] = recent_post['created']
            post['subject'] = recent_post['subject']
            post['content'] = recent_post['content']
            
            def trim_children(c):
                r = []
                for child in c:
                    d = dict((key,value) for key, value in child.iteritems() if key in ['uid', 'created', 'updated', 'type', 'children', 'subject'])
                    d['children'] = trim_children(d['children'])
                    r.append(d)
                    
                return r
                    
            post['children'] = trim_children(r['children'])
            
            posts.append(post)
                
        posts = self.add_names(posts)
        
        m.drop('posts')
        m.insert_many('posts', posts)
        
        print 'Update Complete.'
        
    def add_names(self, posts):
        '''Add names to posts based on uid
        Args:
            folder (string) -- folder to add names to
        '''     
                
        # get all uids
        def get_uids(posts, uids = []):
            '''recursive function to get all uids
            '''
            if hasattr(posts, 'iteritems'):
                for key, value in posts.items():
                    if(key == 'uid'):
                        uids.append(value)
                    elif isinstance(value, dict):
                        get_uids(value, uids)
                    elif isinstance(value, list):
                        for i in value:
                            get_uids(i, uids)
            return uids
         
        uids = []
          
        for post in posts:
            uids = list(set(get_uids(post)))
         
        #get list of users    
        users = self.get_users(uids)
        
        # insert names into posts where uid exists     
        def insert_names(post):
            '''resursive function to insert name where uid exists
            '''
            if(hasattr(post, 'iteritems')):
                for key, value in post.items():
                
                    if(key == 'uid'):
                        exists = False
                        for user in users:
                            if(user['id'] == value):
                                exists = True
                                post['name'] = user['name']
                                break
                                
                        if(not exists):
                            post['name'] = '(anonymous)'
                                
                    elif(key == 'author_id'):
                        exists = False
                        for user in users:
                            if(user['id'] == value):
                                exists = True
                                post['author'] = user['name']
                                break
                        
                        if(not exists):
                            post['author'] = '(anonymous)'
                                
                    if(isinstance(value, dict)):
                        insert_names(value) 
                    elif(isinstance(value, list)):
                        for i in value:
                            insert_names(i)
                return post
             
        posts_with_names = []
        for post in posts:
            post = insert_names(post)
            posts_with_names.append(post)
            
        return posts_with_names   
        
    def get_users(self, uids):
        '''Get list of users from Piazza, directly from Piazza API
        Args:
            uids (list) -- user ids
        Returns:
            (dict) -- users information
        '''
        
        post_data = json.dumps({
            'method': 'network.get_users',
            'params': {
                'ids': uids,
                'nid': self.class_id
            }
        })
        
        print 'Getting user names.'
        
        r = requests.post(self.api_url, data = post_data, cookies = self.login_cookie)
        
        # add to db
        self.add_users(r.json()['result'])
        
        return r.json()['result']
        
    def add_users(self, users):
        '''Add list of users to db
        Args:
            users (dict) -- user information
        '''
        m = PiazzaMongo()
        
        for user in users:
            m.insert('piazza_users', user)
