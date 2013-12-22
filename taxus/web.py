import core
import web


class CachedContent(core.INode):

    """
    This is a pointer to a local path, that may or may not contain a cached
    resource. If (fully) retrieved, the entities body is located at local_path. 
    TODO: The entity headers can be reconstructed from DB and/or metafile or resource is filed as-is.
    Complete header information should be mantained when a CachedContent record is created. 
    """

    __tablename__ = 'cnt'
    __mapper_args__ = {'polymorphic_identity': 'inode:cached-resource'}

    content_id = Column('id', Integer, ForeignKey('inodes.id'), primary_key=True)

    cid = Column(String(255), index=True, unique=True)
    size = Column(Integer, nullable=False)
    "The length of the raw data stream. "
    charset = Column(String(32))
    ""
    partial = Column(Boolean)
    # RFC 2616 headers
    etag = Column(String(255))
    expires = Column(DateTime)
    encodings = Column(String(255))


class Status(core.Node):

    """
    Made this a node so it can be annotated, and perhaps expanded in the future
    to map equivalent codes in different protocols.
    """

    __tablename__ = "status"
    __mapper_args__ = {'polymorphic_identity': 'status'}

    status_id = Column('id', Integer, ForeignKey('nodes.id'), primary_key=True)

    http_code = Column(Integer, unique=True)

    #ref = Column(Integer, ForeignKey('nodes.id'))
    #description = Column(Text, index=True)


class Resource(core.Node):

    """
    A generic resource description. A (web) document.
    Normally a subclass should be used for instances, choose between Invariant 
    if the document ought not to change,
    or choose Variant to indicate a more dynamic resource.
    Invariant resources are generally non-negotiated, but sometimes 
    a specific representation may be retrieved through negotiation on 
    an associated Variant resource.
    """

    __tablename__ = 'res'
    __mapper_args__ = {'polymorphic_identity': 'resource'}

    resource_id = Column('id', Integer, ForeignKey('nodes.id'), primary_key=True)

    status_id = Column(ForeignKey('status.http_code'), index=True)
    status = relationship(Status, primaryjoin=status_id == Status.http_code)

    locator_id = Column(ForeignKey('ids_lctr.id'), index=True)
    location = relationship(web.Locator, primaryjoin=locator_id == Locator.lctr_id)
    "Content-Location. , size=0"

    last_access = Column(DateTime)
    last_modified = Column(DateTime)
    last_update = Column(DateTime)

    # RFC 2616 headers
    allow = Column(String(255))

    # extension_headers  = Column(String())


#resource_variant_table = Table('resource_variant', SqlBase.metadata,
#    Column('res_ida', Integer, ForeignKey('res.id'), primary_key=True),
#    Column('vres_idb', Integer, ForeignKey('vres.id'), primary_key=True),
##    mysql_engine='InnoDB', 
##    mysql_charset='utf8'
#)


class Invariant(Resource):

    """
    A resource consisting of a single datastream. 
    As a general rule, Invariants should not change their semantic content,
    but may allow differation in the codec stack used.

    Ideally, a Variant can capture all parameters of an Resource
    and with that manage all possible Invariants.
    """

    __tablename__ = 'ivres'
    __mapper_args__ = {'polymorphic_identity': 'resource:invariant'}

    invariant_id = Column('id', Integer, ForeignKey('res.id'), primary_key=True)

    content_id = Column(Integer, ForeignKey('cnt.cid'), index=True)
    content = relationship(CachedContent,
            primaryjoin=content_id==CachedContent.cid)
    "A specification of the contents. "

    # RFC 2616 headers
    language = Column(String(255))
    mediatype = Column(String(255))


class Variant(Resource):

    """
    A resource the content of which comes with several variations, such as
    output format, natural language, quality indicators, and/or other features.

    Mechanisms for variation include client-negotiated capabilities such as 
    peripheral abilities to render or interact with specific media/services.
    """

    __tablename__ = 'vres'
    __mapper_args__ = {'polymorphic_identity': 'resource:variant'}

    variant_id = Column('id', Integer, ForeignKey('res.id'), primary_key=True)

    # FIXME: vary information not stored
    # Structure for vary is given in RFC draft on HTTP TCN and RVSA. 

    # descriptions - many-to-may to Description.variants


