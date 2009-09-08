#!/usr/bin/env python

# testall.py [py | tst]

import os, os.path
import sys
import subprocess
import traceback
import setpath

python_path = setpath.setpath(__file__)
#print python_path, "added to sys.path"

fix_path = r"""
import setpath

setpath.setpath(%r)
""" % (__file__,)

def call(input):
    child = subprocess.Popen((sys.executable,),
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    input = fix_path + input
    #sys.stderr.write("call: input is %r\n" % (input,))

    out = child.communicate('\n'.join(line.strip()
                                      for line in input.split('\n')))[0]
    lines = out.split('\n')
    while len(lines) > 0 and not lines[-1]: del lines[-1]
    #print "lines:", lines
    for line in lines[:-1]: print line
    if lines:
        return tuple(int(x) for x in lines[-1].split())
    return 1, 0

def usage():
    sys.stderr.write("usage: testall.py [py | tst]\n")
    sys.exit(2)

def run():
    if len(sys.argv) > 2: usage()

    do_py = do_tst = True

    if len(sys.argv) == 2:
        if sys.argv[1] == 'py': do_tst = False
        elif sys.argv[1] == 'tst': do_py = False
        else: usage()

    errors = 0
    tests = 0
    files = 0

    cwd = os.getcwd()
    if cwd.startswith(python_path + os.sep):
        module_prefix = cwd[len(python_path) + 1:].replace(os.sep, '.') + '.'
        if os.sep != '/': module_prefix = module_prefix.replace('/', '.')
    else:
        assert cwd == python_path, \
               "testall.py: must be executed within " \
               "the project directory structure"
        module_prefix = ''

    for dirpath, dirnames, filenames in os.walk('.'):
        if '.hg' in dirnames: dirnames.remove('.hg')
        if 'build' in dirnames: dirnames.remove('build')
        for filename in filenames:
            if filename == 'setup_setpath.py' or filename == 'setup.py':
                continue
            path = os.path.join(dirpath, filename)
            try:
                if do_py and filename.endswith('.py'):
                    print "Testing", path
                    arg = os.path.normpath(path[:-3])
                    arg = arg.replace(os.sep, '.')
                    if os.sep != '/': arg = arg.replace('/', '.')
                    arg = module_prefix + arg

                    files += 1
                    e, t = call("""
                        import %(modpath)s
                        %(modpath)s.doing_doctest = True
                        import doctest

                        ans = doctest.testmod(%(modpath)s)
                        print ans[0], ans[1]
                    """ % {'modpath': arg})
                elif do_tst and filename.endswith('.tst'):
                    print "Testing", path
                    files += 1
                    e, t = call("""
                        import doctest

                        ans = doctest.testfile('%(path)s', False)
                        print ans[0], ans[1]
                    """ % {'path': path})
                else:
                    e = t = 0
            except Exception:
                e, t = 1, 0
                traceback.print_exc()
            errors += e
            tests += t

    print "Files: %d, Tests: %d, Errors: %d" % (files, tests, errors)
    sys.exit(errors)

if __name__ == "__main__":
    run()
