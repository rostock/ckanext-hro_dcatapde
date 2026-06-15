import datetime
import json
import os

from ckanext.dcat.profiles import RDFProfile
from ckanext.dcat.utils import resource_uri
from ckantoolkit import config
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDF, SKOS, XSD



# copied from ckanext.dcat.profiles
ADMS = Namespace('http://www.w3.org/ns/adms#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
GSP = Namespace('http://www.opengis.net/ont/geosparql#')
LOCN = Namespace('http://www.w3.org/ns/locn#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
TIME = Namespace('http://www.w3.org/2006/time')
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')

# custom namespaces
DCATAP = Namespace('http://data.europa.eu/r5r/')
DCATDE = Namespace('http://dcat-ap.de/def/dcatde/')
DCATDE_LIC = Namespace('http://dcat-ap.de/def/licenses/')
MDRLANG = Namespace('http://publications.europa.eu/resource/authority/language/')
MDRTHEME = Namespace('http://publications.europa.eu/resource/authority/data-theme/')

IANA = 'https://www.iana.org/assignments/media-types/'
GEOJSON = IANA + 'application/vnd.geo+json'
ZIP = IANA + 'application/zip'


namespaces = {
  # copied from ckanext.dcat.profiles
  'adms': ADMS,
  'dcat': DCAT,
  'dct': DCT,
  'foaf': FOAF,
  'gsp': GSP,
  'locn': LOCN,
  'owl': OWL,
  'skos': SKOS,
  'spdx': SPDX,
  'time': TIME,
  'vcard': VCARD,

  # custom namespaces
  'dcatap': DCATAP,
  'dcatde': DCATDE,
  'dcatde-lic': DCATDE_LIC,
  'mdrlang': MDRLANG,
  'mdrtheme': MDRTHEME
}


# import JSON mapping files
PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)

def load_mapping(filename):
  with open(os.path.join(DIR_PATH, 'mappings', filename)) as f:
    return json.load(f)

ALGORITHM_MAPPING = load_mapping('algorithms.json')
CATEGORY_MAPPING = load_mapping('categories.json')
FORMAT_MAPPING = load_mapping('formats.json')
GEOCODING_MAPPING = load_mapping('geocodings.json')
HVD_CATEGORY_MAPPING = load_mapping('hvd-categories.json')
LANGUAGE_MAPPING = load_mapping('languages.json')
LICENSE_MAPPING = load_mapping('licenses.json')


# language
language = config.get('ckan.locale_default', 'en')
MDRLANG_LANGUAGE = LANGUAGE_MAPPING.get(language)


class DCATAPdeHROProfile(RDFProfile):

  def __init__(self, graph, compatibility_mode=False):
    super().__init__(graph, compatibility_mode)

    for prefix, namespace in namespaces.items():
      self.g.bind(prefix, namespace)


  def graph_from_catalog(self, catalog_dict, catalog_ref):
    g = self.g

    # dct:language
    if MDRLANG_LANGUAGE:
      g.remove((catalog_ref, DCT.language, Literal(language)))
      g.add((catalog_ref, DCT.language, URIRef(MDRLANG + MDRLANG_LANGUAGE)))


  def parse_dataset(self, dataset_dict, dataset_ref):
    return dataset_dict


  def graph_from_dataset(self, dataset_dict, dataset_ref):
    g = self.g
    dist_additons = {}
    extras_dict = {
      e['key']: e['value']
      for e in dataset_dict.get('extras', [])
    }

    # dcat:landingPage
    g.add((dataset_ref, DCAT.landingPage, URIRef(dataset_ref)))

    # dcatap:hvdCategory and dcatap:applicableLegislation
    hvd_category = None
    extras_hvd_category = extras_dict.get('hvd_category')
    if extras_hvd_category is not None:
      hvd_category = HVD_CATEGORY_MAPPING.get(extras_hvd_category, None)
      if hvd_category is not None:
        g.add((dataset_ref, DCATAP.hvdCategory, URIRef(hvd_category)))
        g.add((dataset_ref, DCATAP.applicableLegislation, URIRef('http://data.europa.eu/eli/reg_impl/2023/138/oj')))

    # dcat:contactPoint
    for contactPoint_ref in g.objects(dataset_ref, DCAT.contactPoint):
      for email in g.objects(contactPoint_ref, VCARD.hasEmail):
        g.remove((contactPoint_ref, VCARD.hasEmail, Literal(email)))
        g.add((contactPoint_ref, VCARD.hasEmail, URIRef('mailto:' + email)))

    # dcat:theme
    groups = self._get_dataset_value(dataset_dict, 'groups')
    for group in groups:
      mdrtheme_groups = CATEGORY_MAPPING[group['name']]
      if mdrtheme_groups:
        for mdrtheme_group in mdrtheme_groups:
          g.add((dataset_ref, DCAT.theme, URIRef(MDRTHEME + mdrtheme_group)))

    # dcatde:contributorID
    contributor_id = config.get('ckanext.hro_dcatapde.contributorid')
    if contributor_id:
      g.add((dataset_ref, DCATDE.contributorID, URIRef('http://dcat-ap.de/def/contributors/' + contributor_id)))

    # dcatde:geocodingDescription
    # dcatde:politicalGeocodingLevelURI
    # dcatde:politicalGeocodingURI
    # dct:spatial
    spatial_refs = list(g.objects(dataset_ref, DCT.spatial))
    geocoding = extras_dict.get('spatial')
    if geocoding:
      for spatial_ref in spatial_refs:
        g.remove((spatial_ref, LOCN.geometry, Literal(geocoding, datatype = GEOJSON)))
        if 'multipolygon' in geocoding:
          geocoding = geocoding.replace('multipolygon', 'MultiPolygon')
        elif 'polygon' in geocoding:
          geocoding = geocoding.replace('polygon', 'Polygon')
        g.add((spatial_ref, LOCN.geometry, Literal(geocoding, datatype = GEOJSON)))
    geocoding_text = extras_dict.get('spatial_text')
    if geocoding_text:
      for spatial_ref in spatial_refs:
        g.remove((spatial_ref, SKOS.prefLabel, Literal(geocoding_text)))
      g.add((dataset_ref, DCATDE.geocodingDescription, Literal(geocoding_text)))
      if geocoding_text in GEOCODING_MAPPING:
        geocoding_object = GEOCODING_MAPPING[geocoding_text]
        if 'politicalGeocodingLevelURI' in geocoding_object:
          g.add((dataset_ref, DCATDE.politicalGeocodingLevelURI, URIRef(geocoding_object['politicalGeocodingLevelURI'])))
        if 'politicalGeocodingURI' in geocoding_object:
          g.add((dataset_ref, DCATDE.politicalGeocodingURI, URIRef(geocoding_object['politicalGeocodingURI'])))

    # dcatde:maintainer
    maintainer = self._get_dataset_value(dataset_dict, 'maintainer')
    maintainer_email = self._get_dataset_value(dataset_dict, 'maintainer_email')
    if maintainer or maintainer_email:
      maintainer_details = BNode()
      g.add((maintainer_details, RDF.type, FOAF.Organization))
      g.add((dataset_ref, DCATDE.maintainer, maintainer_details))
      if maintainer:
        g.add((maintainer_details, FOAF.name, Literal(maintainer)))
      if maintainer_email:
        g.add((maintainer_details, FOAF.mbox, Literal(maintainer_email)))

    # dct:accessRights
    # hard coded URI since an open data portal is publishing open and thus public data anyway
    g.add((dataset_ref, DCT.accessRights, URIRef('http://publications.europa.eu/resource/authority/access-right/PUBLIC')))

    # dct:conformsTo
    g.add((dataset_ref, DCT.conformsTo, URIRef(DCATDE)))

    # dct:creator
    creator = self._get_dataset_value(dataset_dict, 'author')
    creator_email = self._get_dataset_value(dataset_dict, 'author_email')
    if creator or creator_email:
      creator_details = BNode()
      g.add((creator_details, RDF.type, FOAF.Organization))
      g.add((dataset_ref, DCT.creator, creator_details))
      if creator:
        g.add((creator_details, FOAF.name, Literal(creator)))
      if creator_email:
        g.add((creator_details, FOAF.mbox, Literal(creator_email)))

    # dct:language
    if MDRLANG_LANGUAGE:
      g.add((dataset_ref, DCT.language, URIRef(MDRLANG + MDRLANG_LANGUAGE)))

    # dct:temporal
    start_date = extras_dict.get('temporal_coverage_from')
    end_date = extras_dict.get('temporal_coverage_to')
    if start_date or end_date:
      temporal_extent = BNode()
      g.add((temporal_extent, RDF.type, DCT.PeriodOfTime))
      if start_date:
        self._add_date_triple(temporal_extent, DCAT.startDate, start_date)
      if end_date:
        self._add_date_triple(temporal_extent, DCAT.endDate, end_date)
      g.add((dataset_ref, DCT.temporal, temporal_extent))

    # attribution for resources (distributions) enhancement
    terms_of_use_raw = extras_dict.get('terms_of_use')
    if terms_of_use_raw:
      terms_of_use = json.loads(terms_of_use_raw)
    else:
      terms_of_use = {}
    if terms_of_use:
      if 'attribution_text' in terms_of_use:
        dist_additons['attribution_text'] = terms_of_use['attribution_text']

    # license maping for resources (distributions) enhancement
    license_id = self._get_dataset_value(dataset_dict, 'license_id')
    if license_id in LICENSE_MAPPING:
      dist_additons['license_id'] = LICENSE_MAPPING[license_id]['dcatde-id']

    # resources (distributions) enhancement
    distribution_refs = list(g.objects(dataset_ref, DCAT.distribution))
    for resource_dict in dataset_dict.get('resources', []):
      resource_uri_val = URIRef(resource_uri(resource_dict))
      distribution_ref = next(
        (d for d in distribution_refs if d == resource_uri_val),
        None
      )
      self.enhance_resource(g, distribution_ref, resource_dict, dist_additons, hvd_category)


  def enhance_resource(self, g, distribution_ref, resource_dict, dist_additons, hvd_category):
    to_add = []
    to_remove = []
    
    def add(s, p, o):
      to_add.append((s, p, o))

    def remove(s, p, o):
      to_remove.append((s, p, o))

    # dcatap:hvdCategory
    # dcatap:applicableLegislation
    if hvd_category is not None:
      add(distribution_ref, DCATAP.hvdCategory, URIRef(hvd_category))
      add(distribution_ref, DCATAP.applicableLegislation, URIRef('http://data.europa.eu/eli/reg_impl/2023/138/oj'))

    # adms:status
    add(distribution_ref, ADMS.status, URIRef('http://purl.org/adms/status/Completed'))

    # dcat:downloadURL
    if resource_dict.get('resource_type') == 'file':
      add(distribution_ref, DCAT.downloadURL, URIRef(resource_dict.get('url')))

    # dcat:mediaType
    media_types = list(g.objects(distribution_ref, DCAT.mediaType))
    for media_type in media_types:
      remove(distribution_ref, DCAT.mediaType, media_type)
      media_type_string = str(media_type)
      if 'rss+xml' in media_type_string:
        media_type_string = 'application/xml'
      elif '+zip' in media_type_string:
        media_type_string = media_type_string.replace('+zip', '')
        # dcat:compressFormat
        add(distribution_ref, DCAT.compressFormat, URIRef(ZIP))
      add(distribution_ref, DCAT.mediaType, URIRef(IANA + media_type_string))

    # dcatde:licenseAttributionByText
    if 'attribution_text' in dist_additons:
      add(distribution_ref, DCATDE.licenseAttributionByText, Literal(dist_additons['attribution_text']))

    # dcatap:availability
    add(distribution_ref, DCATAP.availability, URIRef('http://publications.europa.eu/resource/authority/planned-availability/STABLE'))

    # dct:conformsTo
    add(distribution_ref, DCT.conformsTo, URIRef(DCATDE))

    # dct:description
    if resource_dict.get('description'):
      add(distribution_ref, DCT.description, Literal(resource_dict.get('description')))

    # dct:format
    for format_string in g.objects(distribution_ref, DCT['format']):
      remove(distribution_ref, DCT['format'], Literal(format_string))
      format_string = format_string.toPython()
      if format_string in FORMAT_MAPPING:
        format_uri = FORMAT_MAPPING[format_string]['uri']
        add(distribution_ref, DCT['format'], URIRef(format_uri))

    # dct:issued
    if resource_dict.get('created'):
      add(distribution_ref, DCT.issued, Literal(resource_dict.get('created'), datatype=XSD.dateTime))

    # dct:language
    if MDRLANG_LANGUAGE:
      remove(distribution_ref, DCT.language, Literal(language))
      add(distribution_ref, DCT.language, URIRef(MDRLANG + MDRLANG_LANGUAGE))

    # dct:license
    if 'license_id' in dist_additons:
      license = DCATDE_LIC[dist_additons['license_id']]
      add(distribution_ref, DCT.license, license)
      add(distribution_ref, DCT.rights, license)

    # dct:modified
    if resource_dict.get('last_modified'):
      add(distribution_ref, DCT.modified, Literal(resource_dict.get('last_modified'), datatype=XSD.dateTime))

    # spdx:checksum
    if resource_dict.get('hash'):
      checksum_refs = list(g.objects(distribution_ref, SPDX.checksum))
      for checksum_ref in checksum_refs:
        add(checksum_ref, RDF.type, SPDX.Checksum)
        if 'sha256' in resource_dict['hash'] and 'sha256' in ALGORITHM_MAPPING:
          algorithm_uri = ALGORITHM_MAPPING['sha256']
          checksum_values = list(g.objects(checksum_ref, SPDX.checksumValue))
          for checksum_value in checksum_values:
            remove(checksum_ref, SPDX.checksumValue, checksum_value)
          raw_hash = resource_dict['hash']
          if ':' in raw_hash:
            raw_hash = raw_hash.split(':', 1)[1]
          add(checksum_ref, SPDX.checksumValue, Literal(raw_hash, datatype=XSD.hexBinary))
          add(checksum_ref, SPDX.algorithm, URIRef(algorithm_uri))

    for t in to_remove:
      g.remove(t)

    for t in to_add:
      g.add(t)


  def _add_date_triple(self, subject, predicate, value, _type = Literal):
    if not value:
      return
    try:
      _date = datetime.datetime.fromisoformat(value)
      self.g.add((subject, predicate, _type(_date.isoformat(), datatype = XSD.dateTime)))
    except ValueError:
      self.g.add((subject, predicate, _type(value)))
