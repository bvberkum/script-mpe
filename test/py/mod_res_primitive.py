import os
import unittest

from zope.interface.verify import verifyObject
from zope.component import getGlobalSiteManager

from script_mpe.res import primitive
from script_mpe.res import iface




class TreeNodeDictTest(unittest.TestCase):

    def setUp(self):
        self.pwd = os.getcwd()

    def test_ifaces(self):
        tree = primitive.TreeNodeDict(u'name')
        verifyObject( iface.Node, tree )
        verifyObject( iface.ITree, tree )

    def test_name(self):
        tree = primitive.TreeNodeDict(u'<root>')
        assert tree.__name__ == u'<root>'

    def test_nodeid(self):
        tree = primitive.TreeNodeDict(u'<root>')
        assert tree.nodeid == u'<root>'

    def test_tree_append(self):
        tree = primitive.TreeNodeDict(u'<root>')
        assert tree.nodeid == u'<root>'
        subnode = primitive.TreeNodeDict(u'<node>')
        tree.append(subnode)
        self.assert_( tree.subnodes == [ subnode ] )

    def test_conform(self):
        tree = primitive.TreeNodeDict(  )

    def test_tree_traverse(self):
        return # FIXME recursing in test_tree_traverse
        tree = primitive.TreeNodeDict(u'<root>')
        subnode = primitive.TreeNodeDict(u'<node>')
        tree.append(subnode)
        #visitor = AbstractHierarchicalVisitor()
        visitor = primitive.NodeIDExtractor()
        r = visitor.traverse(tree)
        self.assert_( list(r) == [ tree, subnode ] )

    def tearDown(self):
        assert self.pwd == os.getcwd(), (self.pwd, os.getcwd())


def test_dictnode_fs_populate(): # TEST creating a dicttree from fs
    root = 'res'
    gsm = getGlobalSiteManager()
    localfs_service = gsm.queryUtility(iface.ILocalNodeService, 'fs')
    return # FIXME test_dictnode_fs_populate
    rootnode = localfs_service(root)
    tree = primitive.TreeNodeDict(None)
# XXX ITraveler + Updater
    visitor = primitive.NodeUpdater(tree)
    traveler = iface.ITraveler(tree)
    tree.travel(rootnode, visitor)
    #list ( visitor.traverse( rootnode ) )

def test_tree():
    from script_mpe import confparse
    root = 'res'
    opts = confparse.Values({})
    tree_init = {}
    res.fs.Dir.tree( root, opts, tree_init )

def test_treenodedict():
    # nodes will be root of a node structure
    nodes = primitive.TreeNodeDict()
    # get the right iface for IHierarchicalVisitor
    tree = iface.ITree( nodes )
# Set up a traveler

def get_cases():
    return [
            TreeNodeDictTest,
            unittest.FunctionTestCase( test_dictnode_fs_populate )
        ]


if __name__ == '__main__':
    #test_tree_traverse()
#    test_dictnode_fs_populate()
    unittest.main()
