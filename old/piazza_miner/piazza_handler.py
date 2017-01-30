import os, sys, datetime

from flask import Flask, render_template, request, send_from_directory
from piazza_extractor import PiazzaExtractor
from piazza_data import PiazzaData
from piazza_setup import PiazzaSetup
from piazza_mongo import PiazzaMongo

from docopt_parser import DocParser, no_flask

class PiazzaHandler:
    def __init__(self, doc):
        '''Check setup, create mongo instance,
            create Flask context, then parse the docopt
        '''
        self.install_complete = False
        self.setup_complete = False
        self.update_complete = False
        
        if(PiazzaSetup().needs_install()):
            self.install()
            self.install_complete = True
            return
            
        if(PiazzaSetup().needs_setup()):
            self.setup()
            self.setup_complete = True
            return

        self.mongo = PiazzaMongo()
        
        if(self.mongo.check_update()):
            self.update()
            self.update_complete = True
            
        self.app = Flask(__name__)
        
        self.docparse = DocParser(doc)
        self.docparse.parse_doc(self)         
            
    def add_filters(self):
        '''Add filters to Flask jinja environment
        '''
        def clean_date(d):
            return datetime.datetime.strptime(d,'%Y-%m-%dT%H:%M:%SZ').strftime('%b %d, %Y %I:%M%p')
        
        self.app.jinja_env.filters['clean_date'] = clean_date
        
    def write_file(self, filename, contents):
        '''Decode and write file
        Args:
            filename (string) -- file name
            contents (string) -- contents to be written
        '''
        print 'Writing "{filename}".'.format(filename = filename)
        
        # create folder if it doesn't exist
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
            
        with(open(filename, 'w+')) as f:
            f.write(contents.encode('utf-8'))
            
    def html_from_template(self, tpl, **kwargs):
        '''wrapper for render_template within flask context
        Args:
            tpl (string) -- template file
        Returns:
            (unicode) -- rendered template
        '''
        with self.app.app_context() as a:
            self.add_filters()
            return render_template(tpl, **kwargs)
            
    def get_uid(self, user):
        '''Get user ID from name
        Args:
            name (string) -- name to search
        Returns:
            (string) -- uid
        '''
        m = PiazzaMongo()
        users = m.search_for_user(user)
        
        if(any(c.isdigit() for c in user)):
            return user
        
        if(len(users) == 0):
            sys.exit('No users found matching "' + user + '".')
            return None
        elif(len(users) == 1):
            print 'User: ' + users[0]['name'] + ', ID: ' + users[0]['id']
            return users[0]['id']
        else:
            while(True):
                print 'Multiple users found. Select one:'
                for i, u in enumerate(users):
                    print str(i) + ') Name: ' + u['name'] + ', ID: ' + u['id']
                
                selection = raw_input('Enter number of user you are looking for ({nums}): '.format(nums = '0-' + str(len(users) - 1)))
                selection = int(selection) if selection.isdigit() else -1
                
                if(int(selection) in range(len(users))):
                    print 'User: ' + users[selection]['name']
                    return users[selection]['id']
                else:
                    print 'Please enter a valid selection.'                   
        
    def get(self, folder = '', comments = False, flask = False):
        '''Get folder posts
        Args:
            folder (folder) -- folder to get
            comments (bool) -- whether or not to include comments
        '''
        d = PiazzaData(self.mongo.find('posts', {'folders': folder}, {'_id': 0}))

        if(flask):
            return render_template('posts.html', posts = d.data, comments = comments)
        else:
            t = self.html_from_template('posts.html', posts = d.data, comments = comments)
            self.write_file('folders/' + folder + '/posts.html', t)         

    def show(self, visual = '', folder = '', flask = False):
        '''Show visual for folder
        Args:
            visual (string) -- visual to show
            folder (string) -- folder posts to analyze
        '''
        js = ['d3.js']
        visual_trimmed = visual.replace(' ', '').replace('-', '')
        if(visual_trimmed == 'wordcloud'):
            d = PiazzaData(self.mongo.find('posts', {'folders': folder}, {'_id': 0})).word_count()
            js += ['d3.layout.cloud.js', 'word-cloud.js']
        elif(visual_trimmed == 'participation'):
            d = PiazzaData(self.mongo.find('posts')).visualize_participation(folder, self.mongo.find('piazza_users', {'role': 'student'}).count())
            js += ['barchart.js'] 
           
        if(flask):
            return render_template('visual.html', visual = visual, folder = folder, data = d.data, js = js, root = '')
        else:
            t = self.html_from_template('visual.html', visual = visual, folder = folder, data = d.data, js = js, root = 'file://' + os.path.dirname(sys.modules[__name__].__file__))
            self.write_file('folders/' + folder + '/' + visual_trimmed + '.html', t)
            
    def folders(self, flask = False):
        '''Display available folders
        '''
        d = PiazzaData(self.mongo.find('posts', {}, {'_id': 0})).get_folders() 
        
        if(not flask):
            d.print_table()      
    
    @no_flask
    def posts(self, cids = '', comments = False):
        '''Display posts by CID
        Args:
            posts (list) -- list of post CID's
        '''
        posts = [p.strip() for p in cids.split(',')] if cids else []
        query = {'$or': [{'cid': int(p)} for p in posts]}

        d = PiazzaData(self.mongo.find('posts', query, {'_id': 0}))
        
        d.print_posts(comments = comments)
    
    @no_flask        
    def install(self):
        '''Setup config and move includes
        '''
        if(not self.install_complete):
            PiazzaSetup().install() 
    
    @no_flask    
    def setup(self):
        '''Setup config and mongodb for Piazza
        '''
        if(not self.setup_complete):
            PiazzaSetup().setup()
    
    @no_flask
    def update(self):
        '''Download all posts
        '''
        if(not self.update_complete):
            e = PiazzaExtractor()
            e.login()
            e.get_all_posts()
     
    def list(self, users = True, role = 'student', flask = False):
        '''List all users, filtered by role
        Args:
            role (string) -- role in piazza
            users (bool) -- list users (not implemented)
        '''
        d = PiazzaData(self.mongo.find('piazza_users', {'role': role}, {'_id': 0}, sort = 'ascending'))
        if(flask):
            return render_template('table.html', fields = d.get_fields(), rows = d.data)
        else:
            d.print_table()
    
    @no_flask    
    def search(self, users = False, post = False, subject = False, everything = False, comment = False, query = '', user = '', uid = ''):
        '''Search for query
        Args:
            users (bool) -- search users
            posts (bool) -- search posts
            subjects (bool) -- search subjects
            query (string) -- search query
            user (string) -- Piazza user name query
            uid (string) -- Piazza user id
        '''
        regex = {'$regex': '.*' + query + '.*', '$options': 'i'}
        
        author_id = ''
        if(user):
            author_id = self.get_uid(user)
        elif(uid):
            author_id = uid
        
        if(everything):
            subject = True
            post = True
            comment = True
            
        if(subject):
            search = {'author_id': author_id} if author_id else {}
            search['subject'] = regex
            d = PiazzaData(self.mongo.find('posts', search, {'_id': 0})).print_posts(highlight = 'subject', highlight_text = query)
            
        if(post):
            search = {'author_id': author_id} if author_id else {}
            search['content'] = regex
            d = PiazzaData(self.mongo.find('posts', search, {'_id': 0})).print_posts(highlight = 'content', highlight_text = query)
 
        if(comment):
            d = PiazzaData(self.mongo.find('posts', {}, {'_id': 0})).search_comments(query, author = author_id).print_comments(highlight = 'subject', highlight_text = query)
            
    def find(self, name = '', flask = False):
        '''Find user id based on name
        Args:
            name (string) -- name to search
        '''
        d = PiazzaData(self.mongo.search_for_user(name)).print_table()
        
    @no_flask        
    def history(self, user = '', uid = '', detailed = False, comments = False):
        '''Show user's post history
        Args:
            user (string) -- Piazza user name query
            uid (string) -- Piazza user id
            detailed (bool) -- whether or not to include full post
            comments (bool) -- whether or not to include comments
        '''
        
        uid = uid if uid else self.get_uid(user)
        
        if(comments):
            d = PiazzaData(self.mongo.find('posts')).print_history(detailed = detailed, comments = comments, author = uid)
        else:
            d = PiazzaData(self.mongo.find('posts', {'author_id': uid})).print_history(detailed = detailed)
    
    @no_flask    
    def completion(self, user = '', uid = ''):
        '''Show user completion, based on "mandatory" folder set in config
        Args:
            user (string) -- Piazza user name query
            uid (string) -- Piazza user id
        '''
        uid = uid if uid else self.get_uid(user)
        
        d = PiazzaData(self.mongo.find('posts', {'author_id': uid})).print_completion()
    
    @no_flask    
    def participation(self, folder = '', detailed = False, posted = ''):
        '''Show participation for Piazza folder
        Args:
            folder (string) -- Piazza folder
        '''
        d = PiazzaData(self.mongo.find('posts', {'folders': folder})).print_participation(folder, self.mongo.find('piazza_users'), detailed = detailed, posted = posted)
    
    def interaction(self, user = '', uid = '', flask = False):
        '''Show user interactions
        Args:
            user (string) -- Piazza user name query
            uid (string) -- Piazza user id
        '''
        uid = uid if uid else self.get_uid(user)
        
        d = PiazzaData(self.mongo.find('posts')).user_interaction(uid)
        
        if(flask):
            return render_template('table.html', fields = d.get_fields(), rows = d.data)
        else:
            d.print_table(order = ['name', 'uid'])
            
    def activity(self, sort = '', flask = False):
        '''Lists users by most active
        '''
        d = PiazzaData(self.mongo.find('posts')).get_activity(sort = sort)
        if(flask):
            return render_template('table.html', fields = d.get_fields(), rows = d.data)
        else:
            d.print_table(order = ['name', 'uid'])
        
    @no_flask    
    def flask(self):
        '''Run flask server
        '''
        self.add_filters()
        self.app.config.update(DEBUG = True) #TODO: remove
        self.docparse.add_routes(self, self.app)
        self.docparse.add_index(self, self.app)
        self.app.run(use_reloader = False)      
