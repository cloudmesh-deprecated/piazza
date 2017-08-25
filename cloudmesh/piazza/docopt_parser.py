import re
from ast import literal_eval
from docopt import docopt
from flask import request


class DocParser:
    def __init__(self, doc):
        self.doc = doc

    def get_arguments(self):
        """Get docopt arguments
        Returns:
            (list) -- docopt arguments
        """
        self.arguments = docopt(self.doc)

        return self.arguments

    def parse_doc(self, handler):
        """Run handler function based on docopt
        Args:
            handler (object) -- object whose methods will be used
        """
        if not hasattr(self, 'arguments'):
            self.arguments = docopt(self.doc)

        lines = self.get_section('usage')
        for line in lines:
            pieces = line.split()[1:]
            func = pieces.pop(0)
            kwargs = {}

            if self.arguments[func]:
                for key, value in self.arguments.iteritems():
                    if value and any(key in p for p in pieces):
                        k = re.sub('[-<>]', '', key)
                        kwargs[k] = value

                getattr(handler, func)(**kwargs)
                break

    def add_index(self, handler, app):
        """Add route for flask index page based on docopt
        Args:
            app (Flask) -- flask app
            handler (object) -- object whose methods will be used
        """
        items = self.get_section('usage')

        html = '<ul>'
        for item in items:
            pieces = item.split()[1:]
            func = pieces[0]

            if hasattr(getattr(handler, func), 'no_flask') and getattr(handler, func).no_flask is True:
                continue

            link = ''
            for piece in pieces:
                link += '/' + re.sub('[-<>]', '', piece)
            html += '<li>{link}</li>'.format(link=link)
        html += '</ul>'

        @app.route('/')
        def home(flask=False):
            return html

    def add_routes(self, handler, app):
        """Add Flask routes based on docopt
        Args:
            handler (object) -- object that route functions will be sent to
            app (Flask) -- flask app
        """
        items = self.get_section('usage')

        for item in items:
            pieces = item.split()[1:]
            func = pieces[0]

            if hasattr(getattr(handler, func), 'no_flask') and getattr(handler, func).no_flask is True:
                continue

            route = ''
            for piece in pieces:
                if piece.startswith('('):
                    combined = '_'.join(piece[1:-1].replace(' ', '').split('|'))
                    route += '/' + '<docopt_required_' + combined + '>'
                elif piece.startswith('['):
                    pass
                elif piece.endswith('...'):
                    route += '/<path:' + piece[1:-4] + '>'
                else:
                    route += '/' + piece

            app.add_url_rule(route, view_func=getattr(handler, func))

        app.url_value_preprocessor(self.add_parameters)
        app.url_value_preprocessor(self.add_required)
        app.url_value_preprocessor(self.add_repeated)

    def add_required(self, endpoint, values):
        """Handle required "or" elements and add to values
        Args:
            endpoint (string) -- method name
            values (dict) -- method arguments
        """
        if endpoint and endpoint != 'static':
            values['flask'] = True
            for key, value in values.items():
                if key.startswith('docopt'):
                    pieces = key.split('_')[2:]
                    new_values = {piece: piece == value for piece in pieces}
                    values.update(new_values)
                    values.pop(key)

    def add_repeated(self, endpoint, values):
        """Handle repeated arguments
        Args:
            endpoint (string) -- method name
            values (dict) -- method arguments
        """
        if endpoint:
            for key, value in values.iteritems():
                if type(value) is unicode and '/' in value:
                    values[key] = value.split('/')

    def add_parameters(self, endpoint, values):
        """Before view function is called, add url parameters to function argument values
        Args:
            endpoint (string) -- method name
            values (dict) -- method arguments
        """
        if endpoint:
            for key, value in request.args.iteritems():
                try:
                    value = literal_eval(value)
                except ValueError:
                    value = value

                values[key] = value

    def get_section(self, section):
        """Get docopt section
        Args:
            section (string) -- section to retrieve
        Returns:
            (list) section
        """
        lines = self.doc.splitlines()
        begin = None
        end = None
        for index, line in enumerate(lines):
            if line.lower().startswith(section):
                begin = index + 1
            elif begin is not None and (line == '' or ':' in line):
                end = index
                break
        return [x.strip() for x in lines[begin:end]]


def no_flask(func):
    """decorator function to prevent flask routing on function
    Args:
        func (function) -- wrapped function
    Returns:
        (function) -- with no_flask attribute
    """
    func.no_flask = True
    return func
