'''Piazza Miner

Usage:
    piazza.py get <folder> [--comments]
    piazza.py show <folder> <visual>
    piazza.py folders
    piazza.py posts <cids> [--comments]
    piazza.py history (--user=<user>|--uid=<uid>) [--detailed --comments]
    piazza.py completion (--user=<user>|--uid=<uid>)
    piazza.py participation <folder> [--posted=<posted>]
    piazza.py list users [--role=<role>]
    piazza.py search (post|subject|comment|everything) <query> [(--user=<user>|--uid=<uid>)]
    piazza.py find <name>
    piazza.py interaction (--user=<user>|--uid=<uid>)
    piazza.py activity [--sort=<sort>]
    piazza.py unanswered
    piazza.py install
    piazza.py setup
    piazza.py update
    piazza.py flask

Options:
    -h --help
    --comments              show/use/include comments
    --detailed              show full post information
    --role=<role>           class role (student, instructor, etc) [default: student]
    --author=<author>       author name/id
    --sort=<sort>           column to sort results by
    --posted=<posted>       filter by whether or not user posted "yes" or "no"
    
Arguments:
    folder:         Piazza folder
    visual:         visualization type to return ("word cloud")
    cids:           post cid's, separated by commas
    user:           user name
    uid:            user id
    name:           user name
    query:          search query
'''
from piazza_handler import PiazzaHandler
       
def main():
    PiazzaHandler(__doc__)    
                 
if __name__ == '__main__':
    main()
