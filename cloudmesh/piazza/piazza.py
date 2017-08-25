"""Piazza Miner

Usage:
    piazza.py get <folder> [--comments]
    piazza.py show <visual> [--folder=<folder> --chart=<chart>]
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
    piazza.py config <section> <item> --value=<value>
    piazza.py --version

Options:
    -h --help
    -v --version            version information
    --comments              show/use/include comments
    --detailed              show full post information
    --folder=<folder>       Piazza folder
    --chart=<chart>         chart type ("bar", "pie", etc) *attempting to force an incompatible type may cause errors
    --role=<role>           class role (student, instructor, etc)
    --author=<author>       author name/id
    --sort=<sort>           column to sort results by
    --posted=<posted>       filter by whether or not user posted ("yes" or "no")
    --value=<value>         new value

Arguments:
    visual:         visualization type to return ("word cloud")
    cids:           post cid's, separated by commas
    user:           user name
    uid:            user id
    name:           user name
    query:          search query
    section:        config section
    item:           config item
"""
from cloudmesh.piazza.piazza_handler import PiazzaHandler


def main():
    PiazzaHandler(__doc__)


if __name__ == '__main__':
    main()
