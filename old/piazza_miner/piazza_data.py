import os, datetime, re, textwrap
from bs4 import BeautifulSoup
import pymongo

import config

class PiazzaData:
    '''Piazza data manipulation/analysis
    '''
    def __init__(self, data = []):
        '''Create the data item with given data
        Args:
            data (list) -- list of piazza data
        '''
        if(type(data) == pymongo.cursor.Cursor):
            data = list(data)
        
        self.data = data
            
    def clean_html(self, html):
        '''Remove HTML tags and encoding
        Args:
            html (string) -- html to clean
        Returns:
            (string) -- without html
        '''
        replace = {
            '\u2018': "'",
            '\u2019': "'",
            '\u201c': '"',
        }
        for key, value in replace.iteritems():
            html = html.replace(key, value)
            
        html = u' '.join(html.split()) # remove space and newlines encoding

        return BeautifulSoup(html, 'html.parser').get_text()
                    
    def word_count(self):
        '''Get word count of self.data 'posts'
        Returns:
            (PiazzaData) -- word: count
        '''
        ignore = ['the', 'for','what', 'which', 'why', 'that', 'and', 'you', 'can', 'also', 'let', 'are', 'any', 'but', 'like', 'all', 'out', 'may', 'get', 'this', 'when', 'some', 'not', 'will', 'use', 'was', 'have', 'there', 'our', 'its', 'how', 'been', 'with', 'has', 'these', 'they', 'each', 'into', 'there', 'who', 'from', 'many', 'one', 'more', 'need', 'would', 'most', 'their', 'about', 'being', 'every', 'where', 'them', 'such', 'using', 'really']
        punc = ['.', ',', '?', '/', '"', "'", '(', ')', '!', '~', '}', ']', ':']
        words = {}
        for item in self.data:
            word_list = self.clean_html(item['content']).split(' ')
            for w in word_list:
                w = w.lower()         
                for p in punc:
                    w = w.replace(p, '') # remove punctuation
                    
                if(w in ignore or w.isdigit() or len(w) < 3 or w.startswith('{') or w.startswith('[') or w.startswith('http') or w.startswith('@')):
                    continue
                elif(w in words):
                    words[w] += 1
                else:
                    words[w] = 1
                    
        tags = []
        for k, v in words.iteritems():
            tags.append({'key': k, 'value': v})
                    
        return PiazzaData({'tags': tags})
          
    def user_interaction(self, uid):
        '''Get user interactions
        Args:
            uid (string) -- user id
        Returns:
            (PiazzaData) -- interactions
        '''
        interactions = []
        for post in self.data:
            followup_uid = ''
            followup_name = ''
            
            if(post['author_id'] == uid):
                user_is_author = True
            else:
                user_is_author = False

            for comment in self.iter_comments(post):
                if('uid' in comment):
                    if(comment['type'] == 'followup'):
                        if(user_is_author and comment['uid'] != uid):
                            interactions.append((comment['uid'], comment['name']))
                        elif(comment['uid'] == uid):
                            interactions.append((post['author_id'], post['author']))

                        followup_uid = comment['uid']
                        followup_name = comment['name'] 
                        
                    elif(comment['type'] == 'feedback' and comment['uid'] == uid):
                        if(followup_uid and followup_uid != uid):
                            interactions.append((followup_uid, followup_name))
                            
                    elif(comment['type'] == 'feedback' and followup_uid == uid):
                        interactions.append((comment['uid'], comment['name']))

        # reduce to count
        counts = []
        for interaction_uid, name in interactions:
            if(interaction_uid == uid):
                continue
              
            exists = False
            for count in counts:
                if(count['uid'] == interaction_uid):
                    exists = True
                    count['count'] += 1
                    
            if(not exists):
                counts.append({'uid': interaction_uid, 'name': name, 'count': 1})
                
        # sort counts descending
        counts = sorted(counts, key = lambda k: k['count'], reverse = True)

        return PiazzaData(counts)
          
    def get_activity(self, sort = ''):
        '''Lists users by most active
        Returns:
            (PiazzaData) -- list of user by activity
        '''
        num_posts = []
        
        for post in self.data:
            exists = False
            for p in num_posts:
                if(post['author_id'] == p['uid']):
                    exists = True
                    if('posts' in p):
                        p['posts'] += 1
                    else:
                        p['posts'] = 1
                     
                    if('likes' in p):
                        p['likes'] += post['good_tags']
                    else:
                        p['likes'] = 0
                        
                    if('favorites' in p):
                        p['favorites'] += post['num_favorites']
                    else:
                        p['favorites'] = 0
                    
            if(not exists):
                num_posts.append({'name': post['author'], 'uid': post['author_id'], 'posts': 1})
                
            for comment in self.iter_comments(post):
                if('uid' not in comment):
                    continue
                exists = False
                for p in num_posts:
                    if(comment['uid'] == p['uid']):
                        exists = True
                        if('comments' in p):
                            p['comments'] += 1
                        else:
                            p['comments'] = 1
                        
                if(not exists):
                    num_posts.append({'name': comment['name'], 'uid': comment['uid'], 'comments': 1})
                    
        for user in num_posts:
            for item in ['likes', 'favorites', 'comments', 'posts']:
                if(item not in user):
                    user[item] = 0
                    
        # sort by number of posts/comments descending
        num_posts = sorted(num_posts, key = lambda k: (k[sort] if sort in k else k['posts'] + k['comments']), reverse = True)

        return PiazzaData(num_posts)    
        
    def print_table(self, order = []):
        '''Prints ascii table from self.data
        Args:
            sort (list) -- list of keys to sort with
        '''
        if(not self.data):
            print 'Table is empty.'
        else:
            # get field names
            fields = []
            for post in self.data:
                fields += post.keys()
            fields = list(set(fields))

            lengths = {x: len(x) + 1 for x in fields}
            
            # sort fields
            for key in reversed(order):
                if key in fields:
                    fields.remove(key)
                    fields = [key] + fields
            
            # get field lengths
            for row in self.data:
                for key, value in row.iteritems():
                    length = len(str(value))
                    if(length > lengths[key]):
                        lengths[key] = length + 1
              
            # add headers            
            rows = [{x: x for x in lengths.keys()}] + self.data
            
            # create table
            table = '=' * (sum(lengths.values()) + len(lengths.values()) * 2 + 1) + '\n'
            for row in rows:
                table += '|'  
                for key in fields:
                    display = str(row[key]) if key in row else ''
                    difference = lengths[key] - len(display)
                    table += difference * ' ' + display + ' |'
                table += '\n='
                for field in fields:
                    table += '=' * (lengths[field] + 1) + '+'
                table = table[:-1] + '='
                table += '\n'
            
            table = table[:-(sum(lengths.values()) + len(lengths.values()) * 2 + 2)]
            table += '=' * (sum(lengths.values()) + len(lengths.values()) * 2 + 1) + '\n'    
            print table
            
    def print_posts(self, highlight = '', highlight_text = '', comments = False):
        '''Print posts
        Args:
            highlight (string) -- item where text needs to be highlighted
            highlight_text (string) -- text to be highlighted
        '''
        for post in self.data:
            content = self.clean_html(post['content'])
            if(highlight == 'content'):
                content = re.sub(highlight_text, lambda m: '\033[4m' + m.group(0) + '\033[0m', content, flags=re.I)
                
            subject = self.clean_html(post['subject'])
            if(highlight == 'subject'):
                subject = re.sub(highlight_text, lambda m: '\033[4m' + m.group(0) + '\033[0m', subject, flags=re.I) 
                         
            print 'Subject: ' + subject
            print 'Author: ' + post['author'] if 'author' in post else '(anonymous)'
            print 'Author ID: ' + str(post['author_id']) if 'author_id' in post else '(none)'
            print 'Post CID: ' + str(post['cid'])
            print 'Created: ' + self.convert_date(post['created'])
            print 'Content: ' + content
            print
            
            if(comments):
                length = 100
                offset = len('Content: ')
            
                for comment in self.iter_comments(post):
                    if(comment['type'] == 'followup'):
                        indent = '\t'
                    elif(comment['type'] == 'feedback'):
                        indent = '\t\t'
                    
                    print indent + 'Author: ' + comment['name'] if 'name' in comment else indent + 'Author: (anonymous)'
                    print indent + 'Created: ' + self.convert_date(comment['created'])           
                    
                    content = self.clean_html(comment['subject']) if 'subject' in comment else '(none)'
                    print indent + 'Content: ' + content[0:(length - offset)]
                    content = [content[i:i+length].strip() + '\n' + indent for i in range(length - offset, len(content), length)]                 
                    print indent + ''.join(content)
            
    def get_fields(self):
        '''Get fields from self.data, for table headers
            Assumes that each item has identical fields
        Returns:
            (list) -- fields in data
        '''
        return self.data[0].keys()
            
    def print_history(self, detailed = False, comments = False, author = ''):
        '''Prints user history
        '''
        if(comments):
            user_posts = []
            for post in self.data:
                if(post['author_id'] == author):
                    copy = post.copy()
                    copy.update({'post_type': 'post'})
                    user_posts.append(copy)
                    
                for comment in self.iter_comments(post):
                    if('uid' in comment):
                        if(comment['uid'] == author):
                            copy = comment.copy()
                            copy['folders'] = post['folders']
                            copy['parent_subject'] = post['subject']
                            copy['parent_cid'] = post['cid']
                            copy.update({'post_type': 'comment'})
                            user_posts.append(copy)
                            
            #sort posts by date descending
            user_posts = sorted(user_posts, key = lambda k: k['created']) 
            
            print 'User has {num} posts (including comments):'.format(num = len(user_posts))
            for post in user_posts:
                if(detailed):
                    if(post['post_type'] == 'post'):
                        print 'Subject: ' + self.clean_html(post['subject'])
                        print 'Author: ' + post['author']
                        print 'Author ID: ' + post['author_id'] if 'author_id' in post else '(none)'
                        print 'Post CID: ' + str(post['cid'])
                        print 'Created: ' + self.convert_date(post['created'])
                        print 'Content: ' + self.clean_html(post['content'])
                        print
                    elif(post['post_type'] == 'comment'):
                        print 'Comment on post: ' + self.clean_html(post['parent_subject'])
                        print 'Parent CID: ' + str(post['parent_cid'])
                        print 'Author: ' + post['name']
                        print 'Created: ' + self.convert_date(post['created'])
                        print 'Content: ' + self.clean_html(post['subject'])
                        print
                else:
                    if(post['post_type'] == 'post'):
                        print 'Posted "' + self.clean_html(post['subject']) + '" in ' + ', '.join(post['folders']) + ' on ' + self.convert_date(post['created'])
                    elif(post['post_type'] == 'comment'):
                        print 'Commented on post "' + self.clean_html(post['parent_subject']) + '" in ' + ', '.join(post['folders']) + ' on ' + self.convert_date(post['created'])
        else:
            print 'User has {num} posts:'.format(num = len(self.data))
            for post in self.data:
                if(detailed):
                    print 'Subject: ' + self.clean_html(post['subject'])
                    print 'Author: ' + post['author']
                    print 'Author ID: ' + post['author_id'] if 'author_id' in post else '(none)'
                    print 'Post CID: ' + str(post['cid'])
                    print 'Created: ' + self.convert_date(post['created'])
                    print 'Content: ' + self.clean_html(post['content'])
                    print
                else:
                    print 'Posted "' + self.clean_html(post['subject']) + '" in ' + ', '.join(post['folders']) + ' on ' + self.convert_date(post['created'])
                             
    def print_completion(self):
        '''Prints user completion information
        '''
        mandatory = config.get('folders', 'mandatory').split(',')
        mandatory = [f.strip() for f in mandatory]
        
        complete = {}
        for post in self.data:
            for folder in mandatory:
                if(folder in post['folders']):
                    complete[folder] = post['created']
                    
        print 'Completion: {percent}%'.format(percent = round((float(len(complete))/len(mandatory)) * 100))
        
        for folder in mandatory:
            if(folder in complete):
                print '"{folder}" completed on {date}'.format(folder = folder, date = complete[folder])
            else:
                print '"{folder}" incomplete'.format(folder = folder)
                
    def visualize_participation(self, folder, num_students):
        '''Get participation for folder
        Args:
            folder (string) -- Piazza folder
            num_students (int) -- number of all (known) students
        '''
        completion = {}
        
        for post in self.data:
            folders = post['folders']
            for f in folders:
                if(f not in completion):
                    completion[f] = []
                completion[f].append(post['author_id'])
        
        total = 0   
        for key, value in completion.iteritems():
            folder_participation = round((float(len(set(value)))/num_students) * 100)
            total += folder_participation
            completion[key] = folder_participation 
            
        average = total / len(completion)
        
        print folder, completion[folder], average
                
        return PiazzaData({'data': [{'Folder': folder, 'Freq': completion[folder]}, {'Folder': 'Average', 'Freq': average}]})
                
    def print_participation(self, folder, users, detailed = False, posted = ''):
        '''print folder participation
        Args:
            folder (string) -- Piazza folder
            users (list) -- list of all (known) users
        '''
        students = [{'uid': u['id'], 'name': u['name'], 'posts': 0, 'comments': 0} for u in users if u['role'] == 'student']
        
        for post in self.data:
            for student in students:
                if(student['uid'] == post['author_id']):
                    student['posts'] += 1
                    break
                    
            for comment in self.iter_comments(post):
                if('uid' in comment):
                    for student in students:
                        if(student['uid'] == comment['uid']):
                            student['comments'] += 1
                            break
                    
        print '"{folder}" student participation: {percent}%'.format(folder = folder, percent = round((float(len([k for k in students if k['posts'] or k['comments']]))/len(students)) * 100))
        
        students = sorted(students, key = lambda x: (x['posts'], x['comments']), reverse = True)
        
        if(posted == 'yes'):
            print 'The following students posted:'
            students = [k for k in students if k['posts'] or k['comments']]
        
        elif(posted == 'no'):
            print 'The following students did not post:'
            students = [k for k in students if not k['posts'] and not k['comments']]          
        
        PiazzaData(students).print_table(order = ['name', 'uid'])
                  
    def iter_comments(self, post):
        '''Iterate through all comments
        Args:
            post (dict) -- post to get comments for
        Returns:
            (generator) -- of comments
        '''
        def get_comments(post):
            '''recursive generator to yield all comments
            '''
            for child in post['children']:
                yield child
               
                for c in get_comments(child):
                    yield c
                    
        return get_comments(post)
        
    def search_comments(self, query, author = ''):
        '''Search comments
        Args:
            query (string) -- to find in comments
            author (string) -- comment author
        Returns:
            (PiazzaData) -- results
        '''
        result = []
        for post in self.data:
            for comment in self.iter_comments(post):
                if('subject' in comment and query in comment['subject']):
                    if(not author):
                        result.append(comment)
                    elif('uid' in comment and comment['uid'] == author):
                        result.append(comment)
                        
        return PiazzaData(result)
        
    def print_comments(self, highlight = '', highlight_text = ''):
        '''Print comments
        Args:
            highlight (string) -- item where text needs to be highlighted
            highlight_text (string) -- text to be highlighted
        '''
        for comment in self.data:
            subject = self.clean_html(comment['subject'])
            if(highlight == 'subject'):
                subject = re.sub(highlight_text, lambda m: '\033[4m' + m.group(0) + '\033[0m', subject, flags=re.I) 
                         
            print 'Author: ' + comment['name'] if 'name' in comment else '(anonymous)'
            print 'Author ID: ' + comment['uid'] if 'uid' in comment else '(none)'
            print 'Comment: ' + subject
            print 'Created: ' + self.convert_date(comment['created'])
            print       
        
    def convert_date(self, date):
        '''Convert date to readable
        Args:
            date (string) -- date
        Returns:
            (string) -- formatted date
        '''
        return datetime.datetime.strptime(date,'%Y-%m-%dT%H:%M:%SZ').strftime('%b %d, %Y %I:%M%p')
