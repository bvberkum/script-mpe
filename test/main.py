import sys
import glob
import importlib
import os
import unittest
import types


def gather_test_modules(path):
    assert path[0] != os.sep, "relative path"
    pwd = os.path.realpath(os.getcwd())
    sys.path.append(os.path.join(pwd, path))
    sys.path.append(pwd)
    os.chdir(path)
    mods = [ importlib.import_module(name[:-3]) for name in glob.glob( '*.py' ) ]
    os.chdir(pwd)
    return mods

def gather_tests(modules):
    tests = []
    loader = unittest.TestLoader()
    for mod in modules:
        for Case in mod.get_cases():
            if isinstance(Case, unittest.FunctionTestCase):
                tests.append( Case )
            elif issubclass(Case, unittest.TestCase):
                tests.append( loader.loadTestsFromTestCase( Case ))
            else:
                print repr(Case)
    return tests


if __name__ == '__main__':
    testmodules = gather_test_modules('test/py')
    print 'Test modules:', len(testmodules)
    testclasses = gather_tests(testmodules)
    print 'Test cases:', len(testclasses)
    testsuite = unittest.TestSuite(testclasses)
    tr = unittest.TextTestRunner(verbosity=2).run(testsuite)
    if tr.errors:
        sys.exit(2)
    if tr.failures:
        sys.exit(1)
