# -*- coding: utf-8 -*-

import datetime
import json
import os

from ckanext.dcat.profiles import RDFProfile
from ckanext.dcat.utils import resource_uri
from ckantoolkit import config
from dateutil.parser import parse as parse_date
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



class DCATAPdeHROProfile(RDFProfile):

  def __init__(self, graph, compatibility_mode=False):
    path = os.path.abspath(__file__)
    dir_path = os.path.dirname(path)

    with open(os.path.join(dir_path, 'mappings', 'algorithms.json')) as json_data:
      self.algorithm_mapping = json.load(json_data)
    with open(os.path.join(dir_path, 'mappings', 'categories.json')) as json_data:
      self.category_mapping = json.load(json_data)
    with open(os.path.join(dir_path, 'mappings', 'formats.json')) as json_data:
      self.format_mapping = json.load(json_data)
    with open(os.path.join(dir_path, 'mappings', 'geocodings.json')) as json_data:
      self.geocoding_mapping = json.load(json_data)
    with open(os.path.join(dir_path, 'mappings', 'hvd-categories.json')) as json_data:
      self.hvd_category_mapping = json.load(json_data)
    with open(os.path.join(dir_path, 'mappings', 'languages.json')) as json_data:
      self.language_mapping = json.load(json_data)
    with open(os.path.join(dir_path, 'mappings', 'licenses.json')) as json_data:
      self.license_mapping = json.load(json_data)

    super(DCATAPdeHROProfile, self).__init__(graph, compatibility_mode)


  def graph_from_catalog(self, catalog_dict, catalog_ref):
    g = self.g

    # dct:language
    language = config.get('ckan.locale_default', 'en')
    if language in self.language_mapping:
      mdrlang_language = self.language_mapping[language]
      g.remove((catalog_ref, DCT.language, Literal(language)))
      g.add((catalog_ref, DCT.language, URIRef(MDRLANG + mdrlang_language)))


  def parse_dataset(self, dataset_dict, dataset_ref):
    return dataset_dict


  def graph_from_dataset(self, dataset_dict, dataset_ref):
    g = self.g
    dist_additons = {}

    # dcat:landingPage
    g.add((dataset_ref, DCAT.landingPage, URIRef(dataset_ref)))

    # dcatap:applicableLegislation
    g.add((dataset_ref, DCATAP.applicableLegislation, URIRef('http://data.europa.eu/eli/reg_impl/2023/138/oj')))

    # dcatap:hvdCategory
    hvd_category = None
    groups = self._get_dataset_value(dataset_dict, 'groups')
    for group in groups:
      hvd_category = self.hvd_category_mapping[group['name']]
      if hvd_category:
        g.add((dataset_ref, DCATAP.hvdCategory, URIRef(hvd_category)))
        break # ignore further groups and thus set only one HVD category

    for prefix, namespace in namespaces.items():
      g.bind(prefix, namespace)

    # dcat:contactPoint
    for contactPoint_ref in g.objects(dataset_ref, DCAT.contactPoint):
      for email in g.objects(contactPoint_ref, VCARD.hasEmail):
        g.remove((contactPoint_ref, VCARD.hasEmail, Literal(email)))
        g.add((contactPoint_ref, VCARD.hasEmail, URIRef('mailto:' + email)))

    # dcat:theme
    groups = self._get_dataset_value(dataset_dict, 'groups')
    for group in groups:
      mdrtheme_groups = self.category_mapping[group['name']]
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
    geocoding = self._get_dataset_value(dataset_dict, 'spatial')
    if geocoding:
      for spatial_ref in g.objects(dataset_ref, DCT.spatial):
        g.remove((spatial_ref, LOCN.geometry, Literal(geocoding, datatype = GEOJSON)))
        if 'multipolygon' in geocoding:
          geocoding = geocoding.replace('multipolygon', 'MultiPolygon')
        elif 'polygon' in geocoding:
          geocoding = geocoding.replace('polygon', 'Polygon')
        g.add((spatial_ref, LOCN.geometry, Literal(geocoding, datatype = GEOJSON)))
    geocoding_text = self._get_dataset_value(dataset_dict, 'spatial_text')
    if geocoding_text:
      for spatial_ref in g.objects(dataset_ref, DCT.spatial):
        g.remove((spatial_ref, SKOS.prefLabel, Literal(geocoding_text)))
      g.add((dataset_ref, DCATDE.geocodingDescription, Literal(geocoding_text)))
      if geocoding_text in self.geocoding_mapping:
        geocoding_object = self.geocoding_mapping[geocoding_text]
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
    language = config.get('ckan.locale_default', 'en')
    if language in self.language_mapping:
      mdrlang_language = self.language_mapping[language]
      g.add((dataset_ref, DCT.language, URIRef(MDRLANG + mdrlang_language)))

    # dct:temporal
    start_date = self._get_dataset_value(dataset_dict, 'temporal_coverage_from')
    end_date = self._get_dataset_value(dataset_dict, 'temporal_coverage_to')
    if start_date or end_date:
      temporal_extent = BNode()
      g.add((temporal_extent, RDF.type, DCT.PeriodOfTime))
      if start_date:
        self._add_date_triple(temporal_extent, DCAT.startDate, start_date)
      if end_date:
        self._add_date_triple(temporal_extent, DCAT.endDate, end_date)
      g.add((dataset_ref, DCT.temporal, temporal_extent))

    # attribution for resources (distributions) enhancement
    terms_of_use = json.loads(self._get_dataset_value(dataset_dict, 'terms_of_use'))
    if terms_of_use:
      if 'attribution_text' in terms_of_use:
        dist_additons['attribution_text'] = terms_of_use['attribution_text'].encode('utf-8')

    # license maping for resources (distributions) enhancement
    license_id = self._get_dataset_value(dataset_dict, 'license_id')
    if license_id in self.license_mapping:
      dist_additons['license_id'] = self.license_mapping[license_id]['dcatde-id']

    # resources (distributions) enhancement
    for resource_dict in dataset_dict.get('resources', []):
      for distribution in g.objects(dataset_ref, DCAT.distribution):
        if str(distribution) == resource_uri(resource_dict):
          self.enhance_resource(g, distribution, resource_dict, dist_additons, hvd_category)


  def enhance_resource(self, g, distribution_ref, resource_dict, dist_additons, hvd_category):

    # dcatap:applicableLegislation
    g.add((distribution_ref, DCATAP.applicableLegislation, URIRef('http://data.europa.eu/eli/reg_impl/2023/138/oj')))

    # dcatap:hvdCategory
    if hvd_category:
      g.add((distribution_ref, DCATAP.hvdCategory, URIRef(hvd_category)))

    # adms:status
    g.add((distribution_ref, ADMS.status, URIRef('http://purl.org/adms/status/Completed')))

    # dcat:downloadURL
    if resource_dict.get('resource_type') and resource_dict.get('resource_type') == 'file':
      g.add((distribution_ref, DCAT.downloadURL, URIRef(resource_dict.get('url'))))

    # dcat:mediaType
    for format_string in g.objects(distribution_ref, DCAT['mediaType']):
      g.remove((distribution_ref, DCAT['mediaType'], Literal(format_string)))
      compressed = False
      if 'rss+xml' in format_string:
        format_string = 'application/xml'
      elif '+zip' in format_string:
        format_string = format_string.replace('+zip', '')
        # dcat:compressFormat
        g.add((distribution_ref, DCAT['compressFormat'], URIRef(ZIP)))
      else:
        format_string = format_string.toPython()
      format_uri = IANA + format_string
      g.add((distribution_ref, DCAT['mediaType'], URIRef(format_uri)))

    # dcatde:licenseAttributionByText
    if 'attribution_text' in dist_additons:
      g.add((distribution_ref, DCATDE.licenseAttributionByText, Literal(dist_additons['attribution_text'])))

    # dcatap:availability
    g.add((distribution_ref, DCATAP.availability, URIRef('http://publications.europa.eu/resource/authority/planned-availability/STABLE')))

    # dct:conformsTo
    g.add((distribution_ref, DCT.conformsTo, URIRef(DCATDE)))

    # dct:description
    if resource_dict.get('description'):
      g.add((distribution_ref, DCT.description, Literal(resource_dict.get('description'))))

    # dct:format
    for format_string in g.objects(distribution_ref, DCT['format']):
      g.remove((distribution_ref, DCT['format'], Literal(format_string)))
      format_string = format_string.toPython()
      if format_string in self.format_mapping:
        format_uri = self.format_mapping[format_string]['uri']
        g.add((distribution_ref, DCT['format'], URIRef(format_uri)))

    # dct:issued
    if resource_dict.get('created'):
      g.add((distribution_ref, DCT.issued, Literal(resource_dict.get('created'), datatype = XSD.dateTime)))

    # dct:language
    language = config.get('ckan.locale_default', 'en')
    if language in self.language_mapping:
      mdrlang_language = self.language_mapping[language]
      g.remove((distribution_ref, DCT.language, Literal(language)))
      g.add((distribution_ref, DCT.language, URIRef(MDRLANG + mdrlang_language)))

    # dct:license
    if 'license_id' in dist_additons:
      g.add((distribution_ref, DCT.license, DCATDE_LIC[dist_additons['license_id']]))
      g.add((distribution_ref, DCT.rights, DCATDE_LIC[dist_additons['license_id']]))

    # dct:modified
    if resource_dict.get('last_modified'):
      g.add((distribution_ref, DCT.modified, Literal(resource_dict.get('last_modified'), datatype = XSD.dateTime)))

    # spdx:checksum
    if resource_dict.get('hash'):
      for checksum_ref in g.objects(distribution_ref, SPDX.checksum):
        for checksum_value in g.objects(checksum_ref, SPDX.checksumValue):
          g.add((checksum_ref, RDF.type, SPDX.Checksum))
          if 'sha256' in resource_dict['hash'] and 'sha256' in self.algorithm_mapping:
            algorithm_uri = self.algorithm_mapping['sha256']
            g.remove((checksum_ref, SPDX.checksumValue, Literal(resource_dict['hash'], datatype = XSD.hexBinary)))
            g.add((checksum_ref, SPDX.checksumValue, Literal(resource_dict['hash'][7:], datatype = XSD.hexBinary)))
            g.add((checksum_ref, SPDX.algorithm, URIRef(algorithm_uri)))


  def _add_date_triple(self, subject, predicate, value, _type = Literal):
    if not value:
        return
    try:
        default_datetime = datetime.datetime(1, 1, 1, 0, 0, 0)
        _date = parse_date(value, default=default_datetime)
        self.g.add((subject, predicate, _type(_date.isoformat(), datatype = XSD.dateTime)))
    except ValueError:
        self.g.add((subject, predicate, _type(value)))
