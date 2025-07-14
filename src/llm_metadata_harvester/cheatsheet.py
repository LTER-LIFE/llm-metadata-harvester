from __future__ import annotations
from typing import Any

GRAPH_FIELD_SEP = "<SEP>"

CHEATSHEETS: dict[str, Any] = {}

CHEATSHEETS["special_interests_croissant"] = """
- description: Description of the dataset.
- license: The license of the dataset. Croissant recommends using the URL of a known license, e.g.,
    one of the licenses listed at https://spdx.org/licenses/.
- name: The name of the dataset.
- creator: The creator(s) of the dataset.
- datePublished: The date the dataset was published.
- keywords: A set of keywords associated with the dataset, either as free text, or a DefinedTerm with
    a formal definition.
- publisher: The publisher of the dataset, which may be distinct from its creator.
- sameAs: The URL of another Web resource that represents the same dataset as this one.
- dateModified: The date the dataset was last modified.
- inLanguage: The language(s) of the content of the dataset.
"""

CHEATSHEETS["special_interests"] = """
- Metadata date: This element contains the date on which the metadata was created or updated. The
    date format is YYYY-MM-DD (with hyphens).
- Metadata language: Language in which the dataset being described is provided. It contains
    the code of the language used in the metadata text. Only the three-letter codes from ISO 639-2/B
    (bibliographic codes) should be used, as defined in ISO 639-2. The code for Dutch is "dut".
- Responsible organization metadata: This element contains the name of the organization responsible
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
        result: Nederlandse organisatie voor toegepast-natuurwetenschappelijk onderzoek (TNO).
- Landing page: A Web page that can be navigated to in a Web browser to gain access to the catalog, 
    dataset, its distributions and/or additional information.
- Title: A name given to the resource.
- Description: Provide detailed information about the dataset, typically at the level of an abstract.
    Be sure to include the entire abstract text, not just a portion of it.
- Unique Identifier: A unique identifier of the resource being described or cataloged. The identifier
    is a text string which is assigned to the resource to provide an unambiguous reference within a
    particular context.
- Resource type: The nature or genre of the resource. The value SHOULD be taken from a well governed
    and broadly recognised controlled vocabulary, such as:
        DCMI Type vocabulary [DCTERMS]
        [ISO-19115-1] scope codes
        Datacite resource types [DataCite]
        PARSE.Insight content-types used by re3data.org [RE3DATA-SCHEMA] (see item 15 contentType)
        MARC intellectual resource types
    Some members of these controlled vocabularies are not strictly suitable for datasets or data
    services (e.g., DCMI Type Event, PhysicalObject; [ISO-19115-1] CollectionHardware, CollectionSession,
    Initiative, Sample, Repository), but might be used in the context of other kinds of catalogs defined
    in DCAT profiles or applications.
- Keywords: Concepts (keywords, classification, or free text terms) that define the dataset or purpose
    (subjects which can be addressed) using the dataset.
- Data creator: An entity that brought into existence the dataset being described. Creators can be people,
    organizations and/or physical or virtual infrastructure (e.g., sensors, software).
- Data contact point: Relevant contact information for the cataloged resource. Use of vCard is recommended
    [VCARD-RDF]. Make sure to include the full name of the contact person/institution and their email address.
- Data publisher: The entity responsible for making the resource available. Resources of type foaf:Agent
    are recommended as values for this property.
- Spatial coverage: The geographical area covered by the dataset. The spatial coverage of a dataset may be
    encoded as an instance of dcterms:Location, or may be indicated using an IRI reference (link) to a
    resource describing a location. It is recommended that links are to entries in a well maintained
    gazetteer such as Geonames.
- Spatial resolution: Minimum spatial separation resolvable in a dataset, measured in meters. If the
    dataset is an image or grid this should correspond to the spacing of items. For other kinds of spatial
    datasets, this property will usually indicate the smallest distance between items in the dataset.
- Spatial reference system: This element contains the Alphanumeric value that indicates the reference system
    used for the dataset. EPSG issues these codes. For the RD, the code 28992 is used. The reference system
    is included with a URI that also contains the code.
    Example: source:
        <gmx:Anchor
        xlink:href="http://www.opengis.net/def/crs/EPSG/0/28992">RD
        </gmx:Anchor>
    result: http://www.opengis.net/def/crs/EPSG/0/28992
- Temporal coverage: The temporal period that the dataset covers. An interval of time that is named or
    defined by its start and end dates.
- Temporal resolution: Minimum time period resolvable in the dataset. If the dataset is a time-series this
    should correspond to the spacing of items in the series. For other kinds of dataset, this property will
    usually indicate the smallest time difference between items in the dataset.
- License: A legal document under which the resource is made available. Text string describing any rights
    information for the dataset being described.
- Access rights: Information about who can access the resource or an indication of its security status.
    Ways in which the dataset may or may not be accessed and used.
- Distribution access URL: A URL of the resource that gives access to a distribution of the dataset.
    E.g., landing page, feed, SPARQL endpoint.
    dcat:accessURL SHOULD be used for the URL of a service or location that can provide access to this
    distribution, typically through a Web form, query or API call.
    dcat:downloadURL is preferred for direct links to downloadable resources.
    If the distribution(s) are accessible only through a landing page (i.e., direct download URLs are not
    known), then the landing page URL associated with the dcat:Dataset SHOULD be duplicated as access URL
    on a distribution (see 5.7 Dataset available only behind some Web page).
- Distribution format: An established standard to which the dataset distribution conforms to. The file
    format of the distribution.  dcat:mediaType SHOULD be used if the type of the distribution is defined
    by IANA [IANA-MEDIA-TYPES].
- Distribution byte size: The size of a distribution in bytes. The size in bytes can be approximated (as
    a non-negative integer) when the precise size is not known. While it is recommended that the size be
    given as an integer, alternative literals such as '1.5 MB' are sometimes used.
"""

CHEATSHEETS["fill_nightly"] = """---Goal---
Given a list of nightly_entities with metadata and their related source texts, fill in missing fields such as
`entity_name` and `description` for each entity.
Use {language} as output language.

---Steps---
1. For each entity, extract the following information from the text:
- entity_name: Provide the specific name of the entity mentioned in the input text. This should be the actual name (e.g., "Microsoft", "Amazon River", "Mona Lisa") and not the generic entity type (e.g., "company", "river", "painting"). Use the same language as the input text. If the text is in English, capitalize the name.
- entity_type: One of the provided types (do not change it).
- description: A short explanation (1 sentence) of what this entity represents or does.

Format each enriched entity as:
("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<description>{tuple_delimiter}<source_id>{tuple_delimiter}<file_path>)

Fill in the `<Nightly Entity Name>` and `<Nightly Inference>` placeholders with actual information or values in the input text.

2. You must output the enriched entities in this format:
("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<description>{tuple_delimiter}<source_id>{tuple_delimiter}<file_path>)

    Use **{record_delimiter}** as the list separator for each entity entry.
    End the output with **{completion_delimiter}**.
    ⚠️ Do **not** use JSON, Python dictionaries, or nested data structures.
    The output must be a **flat string list**, matching the format exactly as shown below.

#############################
---Real Data---
######################
---Data---
Entities: {nightly_entities}
Text:
{input_text}
######################

######################
Output:"""


CHEATSHEETS["nightly_entity_template"] = """
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Metadata date"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Metadata language"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Responsible organization metadata"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Landing page"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Title"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Description"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Unique Identifier"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Resource type"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Keywords"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Data creator"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Data contact point"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Data publisher"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Spatial coverage"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Spatial resolution"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Spatial reference system"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Temporal coverage"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Temporal resolution"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"License"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Access rights"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Distribution access URL"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Distribution format"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"Distribution byte size"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
"""

CHEATSHEETS["nightly_entity_template_croissant"] = """
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"description"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"license"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"name"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"creator"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"datePublished"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"keywords"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"publisher"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"sameAs"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"dateModified"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"inLanguage"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}
"""

CHEATSHEETS["post_processing"] = """
---Goal---
Given a list of entities with metadata and related descriptive texts, extract concise information for each entity.
Use {language} as the output language even if input language is not in {language}.

---Input Format---
The input consists of a list of tuples in the following format:
("entity"{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>){record_delimiter}
The metadata information for each entity is embedded within the description text.

---Steps---
1. For each tuple, identify the entity and analyze its corresponding description.
2. From the description, extract the concise information relevant to the entity.
    For example, given the text "A0h06_NlSEuNlium5OO3FA, The unique identifier for the metadata record is A0h06_NlSEuNlium5OO3FA." and entity "Unique Identifier".
    the related information should be "A0h06_NlSEuNlium5OO3FA"
    If the description does not contain the relevant information, return "N/A". If the description contains mulitple pieces of information, combine them into a single string.

2. Output the enriched list in the same tuple format:
("entity"{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_info>)

    Use **{record_delimiter}** as the list separator for each entity entry.
    End the output with **{completion_delimiter}**.
    ⚠️ Do **not** use JSON, Python dictionaries, or nested data structures.
    The output must be a **flat string list**, matching the format exactly as shown below.

#############################
---Real Data---
######################
---Data---
Input: {input_entities}

######################
Output:"""