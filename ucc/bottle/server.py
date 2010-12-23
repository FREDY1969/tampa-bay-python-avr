# server.py

import os
import collections
import webbrowser
import bottle

from ucc.word import top_package, xml_access
from ucc import config

from bottle import (get, post, view, request, response, run,
                    send_file, redirect, abort,
                   )

Bottle_dir = os.path.dirname(__file__)
Static_dir = os.path.join(Bottle_dir, 'static')
Root_dir = os.path.dirname(os.path.dirname(Bottle_dir))

bottle.TEMPLATE_PATH = [os.path.join(Bottle_dir, 'views'),]
bottle.debug(True)

packages_info_class = collections.namedtuple('packages_info_class',
                        "packages_name, writable, packages_dir, package_names")

# list of packages_info_class
Packages_dirs = []

Current_package = None

def lookup_packages(packages_name):
    for packages_info in Packages_dirs:
        if packages_name == packages_info.packages_name:
            return packages_info
    raise ValueError("packages {} not found".format(packages_name))

def redirect_to_word(packages_name, package_name, word=None):
    if word is None:
        redirect('/{}/{}'.format(packages_name, package_name))
    else:
        redirect('/{}/{}/{}'.format(packages_name, package_name, word))

@get('/static/:filename#.*#')
def static(filename):
    send_file(filename, root=Static_dir)

@get('/')
@view('top')
def top():
    return {'packages_dirs': Packages_dirs}

@post('/create/:packages_name')
def create_package(packages_name):
    package_name = request.forms['name']
    print("create_package", packages_name, package_name)
    redirect('/')

@post('/create_word/:packages_name/:package_name')
def create_word(packages_name, package_name):
    decl_packages_name = request.forms['decl_packages_name']
    decl_package_name = request.forms['decl_package_name']
    decl_word = request.forms['decl_word']
    word_name = request.forms['name']
    print("create_word", packages_name, package_name, word_name)
    print("  of type", decl_packages_name, decl_package_name, decl_word)
    redirect_to_word(packages_name, package_name, word_name)

@get('/compile/:packages_name/:package_name')
@get('/compile/:packages_name/:package_name/:word')
def compile(packages_name, package_name, word=None):
    print("compile", packages_name, package_name, word)
    redirect_to_word(packages_name, package_name, word)

@get('/load/:packages_name/:package_name')
@get('/load/:packages_name/:package_name/:word')
def load(packages_name, package_name, word=None):
    print("load", packages_name, package_name, word)
    redirect_to_word(packages_name, package_name, word)

@post('/update_answers/:packages_name/:package_name/:word')
def update_answers(packages_name, package_name, word):
    print("update_answers", packages_name, package_name, word)
    for name, value in request.forms.items():
        print(name, value)
    redirect_to_word(packages_name, package_name, word)

@post('/update_text/:packages_name/:package_name/:word')
def update_text(packages_name, package_name, word):
    print("update_text", packages_name, package_name, word)
    new_text = request.forms['text']
    print("text", new_text)
    redirect_to_word(packages_name, package_name, word)

@get('/:packages_name/:package_name')
@get('/:packages_name/:package_name/:word')
@view('word')
def open_package(packages_name, package_name, word=None):
    global Current_package
    if not Current_package or \
       Current_package.packages[-1].package_name != \
           "{}.{}".format(packages_name, package_name):
        packages_info = lookup_packages(packages_name)
        if package_name not in packages_info.package_names:
            raise ValueError("package {} not in {}"
                             .format(package_name, packages_name))
        Current_package = \
          top_package.top(os.path.join(packages_info.packages_dir,
                                       package_name))
        print("Current_package", Current_package.packages[-1].package_name)
    if word:
        word_word = Current_package.get_word_by_label(word)
        print("word_word", word_word)
        print("kind", word_word.kind_obj)
    else:
        word_word = None
    return {'packages_name': packages_name,
            'package_name': package_name,
            'word': word,
            'index': (
                ('ucclib', 'built-in', 'assembler-word', ()),
                ('ucclib', 'built-in', 'const', ()),
                ('ucclib', 'built-in', 'function', ()),
                ('ucclib', 'built-in', 'input-pin', ()),
                ('ucclib', 'built-in', 'output-pin', ('led-pin',)),
                ('ucclib', 'built-in', 'task', ('run',)),
                ('ucclib', 'built-in', 'var', ()),
              ),
            'questions': (
                ('string', 'argument', 0, 'infinite', ()),
              ),
            'word_word': word_word,
            'text':     # None if this word never has text
'''repeat:
    toggle led-pin
    repeat 800:
        repeat 1000: pass
''',

           }

def start(host, port, packages_name=None, package_name=None):
    global Config, Packages_dirs

    Config = config.load()

    ucc_dir = os.path.expanduser(Config.get('user', 'ucc_dir'))

    if not os.path.exists(ucc_dir):
        os.mkdir(ucc_dir)
        xml_access.write_package_list((), ucc_dir)

    if not os.path.exists(os.path.join(ucc_dir, 'packages.xml')):
        xml_access.write_package_list((), ucc_dir)

    Packages_dirs = [
      packages_info_class(
        packages_name=packages_name,
        writable=writable,
        packages_dir=packages_dir,
        package_names={package_name
                       for package_name
                        in xml_access.read_package_list(packages_dir)}
      )
      for packages_name, packages_dir, writable in (
          ('user', ucc_dir, True),
          ('examples', os.path.join(Root_dir, 'examples'), False),
          ('ucclib', os.path.join(Root_dir, 'ucclib'), False),
        )
    ]

    if package_name is None:
        webbrowser.open("http://{host}:{port}/".format(host=host, port=port), 2)
    else:
        if packages_name is None:
            for packages_info in Packages_dirs:
                if package_name in packages_info.package_names:
                    if packages_name is None:
                        packages_name = packages_info.packages_name
                    else:
                        raise AssertionError(
                                "duplicate package {}, in {} and {}"
                                .format(package_name, packages_name,
                                        packages_info.packages_name))
            if packages_name is None:
                raise AssertionError(
                        "package {} not found".format(package_name))
        webbrowser.open("http://{host}:{port}/{packages_name}/{package_name}"
                          .format(host=host, port=port,
                                  packages_name=packages_name,
                                  package_name=package_name),
                        2)
    run(host=host, port=port)
