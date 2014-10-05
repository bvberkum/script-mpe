"""
Docs are in taxus/__init__
"""
from datetime import datetime

import zope.interface
from sqlalchemy import Column, Integer, String, Boolean, Text, \
    ForeignKey, Table, Index, DateTime
#from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import relationship, backref

import iface
from init import SqlBase
from util import ORMMixin

from script_mpe import lib, log




# mapping table for Node *-* Node
#nodes_nodes = Table('nodes_nodes', SqlBase.metadata,
#    Column('nodes_ida', Integer, ForeignKey('nodes.id'), nullable=False),
#    Column('nodes_idb', Integer, ForeignKey('nodes.id'), nullable=False),
#    Column('nodes_idc', Integer, ForeignKey('nodes.id'))
#)

class Node(SqlBase, ORMMixin):

    """
    Provide lookup on numeric ID, name (non-unique) and standard dates.
    """

    zope.interface.implements(iface.Node)

    __tablename__ = 'nodes'

    # Numeric ID
    node_id = Column('id', Integer, primary_key=True)

    # Node type
    ntype = Column(String(36), nullable=False, default="node")
    __mapper_args__ = {'polymorphic_on': ntype,
            'polymorphic_identity': 'node'}

    # Unique node Name (String ID)
    name = Column(String(255), nullable=False, index=True, unique=True)

    space_id = Column(Integer, ForeignKey('spaces.id'))
    space = relationship(
            'Space', 
            #primaryjoin='Node.space_id == Space.space_id'
            backref='children', 
#            remote_side='spaces.id',
#            foreign_keys=[space_id]
        )

    date_added = Column(DateTime, index=True, nullable=False)
    last_updated = Column(DateTime, index=True, nullable=False)
    deleted = Column(Boolean, index=True, default=False)
    date_deleted = Column(DateTime)

    def init_defaults(self):
        if not self.date_added:
            self.last_updated = self.date_added = datetime.now()
        elif not self.last_updated:
            self.last_updated = datetime.now()

    @classmethod
    def default_filters(Klass):
        return (
            ( Klass.deleted == False ),
        )

    def __repr__(self):
        return "<%s at %s for %r>" % (lib.cn(self), hex(id(self)), self.name)

    def __str__(self):
        return "%s for %r" % (lib.cn(self), self.name)


groupnode_node_table = Table('groupnode_node', SqlBase.metadata,
    Column('groupnode_id', Integer, ForeignKey('groupnodes.id'), primary_key=True),
    Column('node_id', Integer, ForeignKey('nodes.id'), primary_key=True)
)

class GroupNode(Node):

    """
    A bit of a stop-gap mechanisms by lack of better containers
    in the short run.
    Like the group nodes in outlines and bookmark files.
    """

    __tablename__ = 'groupnodes'
    __mapper_args__ = {'polymorphic_identity': 'group'}
    group_id = Column('id', Integer, ForeignKey('nodes.id'), primary_key=True)

    subnodes = relationship(Node, secondary=groupnode_node_table, backref='supernode')
    root = Column(Boolean)


class Folder(GroupNode):

    __tablename__ = 'folders'

    __mapper_args__ = {'polymorphic_identity': 'folder'}
    folder_id = Column('id', Integer, ForeignKey('groupnodes.id'), primary_key=True)


class ID(SqlBase, ORMMixin):

    """
    A global system identifier.
    """

    zope.interface.implements(iface.IID)

    __tablename__ = 'ids'
    id_id = Column('id', Integer, primary_key=True)

    idtype = Column(String(50), nullable=False)
    __mapper_args__ = {'polymorphic_on': idtype}

    global_id = Column(String(255), index=True, unique=True, nullable=False)
    """
    With regard to x-db deployment, not using string ID as or in primary key 
    for table, even while that makes sense to me.
    """

    date_added = Column(DateTime, index=True, nullable=False)
    last_updated = Column(DateTime, index=True, nullable=False)
    deleted = Column(Boolean, index=True, default=False)
    date_deleted = Column(DateTime)

    def init_defaults(self):
        if not self.date_added:
            self.last_updated = self.date_added = datetime.now()
        elif not self.last_updated:
            self.last_updated = datetime.now()

    def __repr__(self):
        return "<%s at %s for %r>" % (lib.cn(self), hex(id(self)), self.global_id)


class Space(ID):

    """
    Spaces segment the Nodeverse. 
    
    An abstraction to deal with segmented storage (ie. different databases,
    hosts).
    """

    __tablename__ = 'spaces'

    __mapper_args__ = {'polymorphic_identity': 'space'}

    space_id = Column('id', Integer, ForeignKey('ids.id'), primary_key=True)

    #host = Column(String)
    #storage_uri = Column(String)
    classes = Column(String)







class Name(Node):

    """
    A local unique identifier.

    XXX: this is a vestige of having non-unique node names,
      currently node names are unique so Name need not be used.. much.
    """

    __tablename__ = 'names'
    __mapper_args__ = {'polymorphic_identity': 'name'}
    name_id = Column('id', Integer, ForeignKey('nodes.id'), primary_key=True)

#    name_id = Column('id', Integer, primary_key=True)

#    nametype = Column(String(50), nullable=False)
#    __mapper_args__ = {'polymorphic_on': nametype, 
#            'polymorphic_identity': 'name'}
#
#    name = Column(String(255), index=True, unique=True)
#
#    date_added = Column(DateTime, index=True, nullable=False)
#    deleted = Column(Boolean, index=True, default=False)
#    date_deleted = Column(DateTime)
#
#    def __str__(self):
#        return "%s at %s having %r" % (lib.cn(self), self.taxus_id(), self.name)
#
#    def __repr__(self):
#        return "<%s at %s with %r>" % (lib.cn(self), hex(id(self)), self.name)


class Tag(Name):

    """
    Tags primarily constitute a name unique within some namespace.
    They may be used as types or as instance identifiers.
    """
    zope.interface.implements(iface.IID)

    __tablename__ = 'names_tag'
    __mapper_args__ = {'polymorphic_identity': 'tag'}

    tag_id = Column('id', Integer, ForeignKey('names.id'), primary_key=True)
    #name = Column(String(255), unique=True, nullable=True)
    #sid = Column(String(255), nullable=True)
    # XXX: perhaps add separate table for Tag.namespace attribute
#    namespaces = relationship('Namespace', secondary=tag_namespace_table,
#        backref='tags')

tags_freq = Table('names_tags_stat', SqlBase.metadata,
        Column('tag_id', ForeignKey('names_tag.id'), primary_key=True),
        Column('node_type', String(36), primary_key=True),
        Column('frequency', Integer)
)

class Topic(Tag):
    """
    A topic describes a subject; a theme, issue or matter, regarding something
    else. 
    XXX: It is the first of a level abstraction for other elementary types like
    inodes or document elements.
    For now, it is a succinct name on the Tag supertype, with an additional
    Text field for further specification.
    
    XXX: a basic type indicator to toggle between a thing or an idea.
    Names are given in singular form, a text field codes the plural for UI use.
    """
    __tablename__ = 'names_topic'
    __mapper_args__ = {'polymorphic_identity': 'topic'}

    topic_id = Column('id', Integer, ForeignKey('names_tag.id'), primary_key=True)
    #key_names = ['topic_id']

    about_id = Column(Integer, ForeignKey('nodes.id'))

    explanation = Column(Text)
    thing = Column(Boolean)
    plural = Column(String)

    # TODO backref from locators of this topic
    # TODO hierarchical relation


doc_root_element_table = Table('doc_root_element', SqlBase.metadata,
    Column('inode_id', Integer, ForeignKey('inodes.id'), primary_key=True),
    Column('lctr_id', Integer, ForeignKey('ids_lctr.id'), primary_key=True)
)

class Document(Node):
    """
    After INode and Resource, the most abstract representation of a (file-based) 
    resource in taxus.
    A document comprises a set of elements in an unspecified further structure.

    Systems may allow muxing or demuxing a document from or resp. to its
    elements, Ie. the document object is interchangable by the set of its
    elements (although Node attributes may not be accounted for).

    sameAs
        Incorporates sameAs from N3 to indicate references that may have
        different access protocols but result in the same object
        (properties/actions)?
    """
    __tablename__ = 'docs'
    __mapper_args__ = {'polymorphic_identity': 'doc'}
    doc_id = Column('id', Integer, ForeignKey('nodes.id'), primary_key=True)
#    elements = relationship('Element', secondary=doc_root_element_table)


#class ReCoDoc(Document):
#    """
#    ree-CO-doc, Recursive Container document describes the way hierarchical
#    container based formats provide a serial view of systems and domain objects.
#
#    Some may be canonical, or ambigious, generic or very specific, etc.
#    It forces serialization and a way to look at the resource as a single
#    stream with discrete, nested elements (iow. XML with either some DOMesque
#    interface or serial access interface). 
#
#    TODO: It implements sameAs to indicate ...
#    """
#    __tablename__ = 'rcdocs'
#    __mapper_args__ = {'polymorphic_identity': 'rcdoc'}
#    rcdoc_id = Column('id', Integer, ForeignKey('docs.id'))
#    host = relationship('Host', primaryjoin="Locator.host_id==Host.host_id",
#        backref='locations')
#
#
#class Element(Node):
#    """
#    Part of a Document.
#
#    XXX: I've allowed for re-use by placing a list of element instances on the
#    Document, instead of coding each element with an origin.
#
#    XXX: Subtypes may specificy how Node attributes map to the element objects
#    and/or additional attributes to consitute an element. E.g. an XML Subtype
#    specifies a list with textnodes and/or elements, besides a tag and attributes.
#    XML only has one rootelement per document.
#    """
#    __tablename__ = 'docelems'
#    __mapper_args__ = {'polymorphic_identity': 'docelem'}
#    docelem_id = Column('id', Integer, ForeignKey('nodes.id'))
#    # not much to say yet. there is a numeric ID, (possibly unique) name,
#    # dates and (possible) subtype. Not much else to say.


#class Schema(Variant):
#    """
#    TODO This would define schema information for or one more namespaces.
#    """
#    __tablename__ = 'schema'
#    __mapper_args__ = {'polymorphic_identity': 'resource:variant:schema'}
#
#    namespaces = []



models = [

        Node, Space,

        GroupNode,

        Document,
        ID,
        Name, Tag, Topic

    ]

