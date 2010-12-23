# server.py

import os
import bottle
from bottle import (get, post, view, request, response, run,
                    send_file, redirect, abort,
                   )

Bottle_dir = os.path.dirname(__file__)
Static_dir = os.path.join(Bottle_dir, 'static')

bottle.TEMPLATE_PATH = [os.path.join(Bottle_dir, 'views'),]
bottle.debug(True)

def redirect_to_word(package_dir, package_name, word=None):
    if word is None:
        redirect('/{}/{}'.format(package_dir, package_name))
    else:
        redirect('/{}/{}/{}'.format(package_dir, package_name, word))

@get('/static/:filename#.*#')
def static(filename):
    send_file(filename, root=Static_dir)

@get('/')
@view('top')
def top():
    return {'package_dirs':
              (('ucclib', ('builtins',)),
               ('examples', ('blinky', 'blinky2')),
               ('user', ())),
           }

@post('/create/:package_dir')
def create_package(package_dir):
    package_name = request.forms['name']
    print("create_package", package_dir, package_name)
    redirect('/')

@post('/create_word/:package_dir/:package_name')
def create_word(package_dir, package_name):
    decl_package_dir = request.forms['decl_package_dir']
    decl_package_name = request.forms['decl_package_name']
    decl_word = request.forms['decl_word']
    word_name = request.forms['name']
    print("create_word", package_dir, package_name, word_name)
    print("  of type", decl_package_dir, decl_package_name, decl_word)
    redirect_to_word(package_dir, package_name, word_name)

@get('/compile/:package_dir/:package_name')
@get('/compile/:package_dir/:package_name/:word')
def compile(package_dir, package_name, word=None):
    print("compile", package_dir, package_name, word)
    redirect_to_word(package_dir, package_name, word)

@get('/load/:package_dir/:package_name')
@get('/load/:package_dir/:package_name/:word')
def load(package_dir, package_name, word=None):
    print("load", package_dir, package_name, word)
    redirect_to_word(package_dir, package_name, word)

@post('/update_answers/:package_dir/:package_name/:word')
def update_answers(package_dir, package_name, word):
    print("update_answers", package_dir, package_name, word)
    new_text = request.forms['text']
    print("text", new_text)
    redirect_to_word(package_dir, package_name, word)

@post('/update_text/:package_dir/:package_name/:word')
def update_text(package_dir, package_name, word):
    print("update_text", package_dir, package_name, word)
    new_text = request.forms['text']
    print("text", new_text)
    redirect_to_word(package_dir, package_name, word)

@get('/:package_dir/:package_name')
@get('/:package_dir/:package_name/:word')
@view('word')
def open_package(package_dir, package_name, word=None):
    return {'package_dir': package_dir,
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
                ('mama',),
              ),
            'text':     # None if this word never has text
'''repeat:
    toggle led-pin
    repeat 800:
        repeat 1000: pass
''',

           }

