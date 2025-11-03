LTER_LIFE_STANDARD = {
    "Metadata date": """This element contains the date on which the metadata was created or updated. The
date format is YYYY-MM-DD (with hyphens).""",

    "Metadata language": """Language in which the dataset being described is provided. It contains
the code of the language used in the metadata text. Only the three-letter codes from ISO 639-2/B
(bibliographic codes) should be used, as defined in ISO 639-2. The code for Dutch is "dut".""",

    "Responsible organization metadata": """This element contains the name of the organization responsible
for the metadata. Use the full written name of the responsible organization. An abbreviation may
be added to the organization name. For correct official government organization names, refer to
the list of government organizations. Preferably, fill in this element as a gmx:Anchor, where the
href attribute points to a URI that describes the organization.
Example: source:
    <Anchor
    xlink:href="https://www.tno.nl/nl/over-tno/organisatie">
        Nederlandse organisatie voor
        toegepast-natuurwetenschappelijk onderzoek (TNO)
    </Anchor>
result: Nederlandse organisatie voor toegepast-natuurwetenschappelijk onderzoek (TNO).""",

    "Landing page": """A Web page that can be navigated to in a Web browser to gain access to the catalog,
dataset, its distributions and/or additional information.""",

    "Title": "A name given to the resource.",

    "Description": """Provide detailed information about the dataset, typically at the level of an abstract.
Be sure to include the entire abstract text, not just a portion of it.""",

    "Unique Identifier": """A unique identifier of the resource being described or cataloged. The identifier
is a text string which is assigned to the resource to provide an unambiguous reference within a
particular context.""",

    "Resource type": """The nature or genre of the resource. The value SHOULD be taken from a well governed
and broadly recognised controlled vocabulary, such as:
    DCMI Type vocabulary [DCTERMS]
    [ISO-19115-1] scope codes
    Datacite resource types [DataCite]
    PARSE.Insight content-types used by re3data.org [RE3DATA-SCHEMA] (see item 15 contentType)
    MARC intellectual resource types
Some members of these controlled vocabularies are not strictly suitable for datasets or data
services (e.g., DCMI Type Event, PhysicalObject; [ISO-19115-1] CollectionHardware, CollectionSession,
Initiative, Sample, Repository), but might be used in the context of other kinds of catalogs defined
in DCAT profiles or applications.""",

    "Keywords": """Concepts (keywords, classification, or free text terms) that define the dataset or purpose
(subjects which can be addressed) using the dataset.""",

    "Data creator": """An entity that brought into existence the dataset being described. Creators can be people,
organizations and/or physical or virtual infrastructure (e.g., sensors, software).""",

    "Data contact point": """Relevant contact information for the cataloged resource. Use of vCard is recommended
[VCARD-RDF]. Make sure to include the full name of the contact person/institution and their email address.""",

    "Data publisher": """The entity responsible for making the resource available. Resources of type foaf:Agent
are recommended as values for this property.""",

    "Spatial coverage": """The geographical area covered by the dataset. The spatial coverage of a dataset may be
encoded as an instance of dcterms:Location, or may be indicated using an IRI reference (link) to a
resource describing a location. It is recommended that links are to entries in a well maintained
gazetteer such as Geonames.""",

    "Spatial resolution": """Minimum spatial separation resolvable in a dataset, measured in meters. If the
dataset is an image or grid this should correspond to the spacing of items. For other kinds of spatial
datasets, this property will usually indicate the smallest distance between items in the dataset.""",

    "Spatial reference system": """This element contains the Alphanumeric value that indicates the reference system
used for the dataset. EPSG issues these codes. For the RD, the code 28992 is used. The reference system
is included with a URI that also contains the code.
Example: source:
    <gmx:Anchor
    xlink:href="http://www.opengis.net/def/crs/EPSG/0/28992">RD
    </gmx:Anchor>
result: http://www.opengis.net/def/crs/EPSG/0/28992""",

    "Temporal coverage": """The temporal period that the dataset covers. An interval of time that is named or
defined by its start and end dates.""",

    "Temporal resolution": """Minimum time period resolvable in the dataset. If the dataset is a time-series this
should correspond to the spacing of items in the series. For other kinds of dataset, this property will
usually indicate the smallest time difference between items in the dataset.""",

    "License": """A legal document under which the resource is made available. Text string describing any rights
information for the dataset being described.""",

    "Access rights": """Information about who can access the resource or an indication of its security status.
Ways in which the dataset may or may not be accessed and used.""",

    "Distribution access URL": """A URL of the resource that gives access to a distribution of the dataset.
E.g., landing page, feed, SPARQL endpoint.
dcat:accessURL SHOULD be used for the URL of a service or location that can provide access to this
distribution, typically through a Web form, query or API call.
dcat:downloadURL is preferred for direct links to downloadable resources.
If the distribution(s) are accessible only through a landing page (i.e., direct download URLs are not
known), then the landing page URL associated with the dcat:Dataset SHOULD be duplicated as access URL
on a distribution (see 5.7 Dataset available only behind some Web page).""",

    "Distribution format": """An established standard to which the dataset distribution conforms to. The file
format of the distribution.  dcat:mediaType SHOULD be used if the type of the distribution is defined
by IANA [IANA-MEDIA-TYPES].""",

    "Distribution byte size": """The size of a distribution in bytes. The size in bytes can be approximated (as
a non-negative integer) when the precise size is not known. While it is recommended that the size be
given as an integer, alternative literals such as '1.5 MB' are sometimes used."""
}