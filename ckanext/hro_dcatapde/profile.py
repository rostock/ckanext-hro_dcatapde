# -*- coding: utf-8 -*-

import os
import json
import pylons

from ckanext.dcat.profiles import RDFProfile
from ckanext.dcat.utils import resource_uri
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDF, RDFS, SKOS


# copied from ckanext.dcat.profiles
ADMS = Namespace('http://www.w3.org/ns/adms#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
GSP = Namespace('http://www.opengis.net/ont/geosparql#')
LOCN = Namespace('http://www.w3.org/ns/locn#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
SCHEMA = Namespace('http://schema.org/')
TIME = Namespace('http://www.w3.org/2006/time')
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')

# custom namespaces
DCATDE = Namespace('http://dcat-ap.de/def/dcatde/1_0/')
DCATDE_LIC = Namespace('http://dcat-ap.de/def/licenses/')
MDRLANG = Namespace('http://publications.europa.eu/resource/authority/language/')
MDRTHEME = Namespace('http://publications.europa.eu/resource/authority/data-theme/')

namespaces = {
  # copied from ckanext.dcat.profiles
  'adms': ADMS,
  'dcat': DCAT,
  'dct': DCT,
  'foaf': FOAF,
  'gsp': GSP,
  'locn': LOCN,
  'owl': OWL,
  'schema': SCHEMA,
  'skos': SKOS,
  'time': TIME,
  'vcard': VCARD,

  # custom namespaces
  'dcatde': DCATDE,
  'dcatde-lic': DCATDE_LIC,
  'mdrlang': MDRLANG,
  'mdrtheme': MDRTHEME
}


class DCATAPdeHROProfile(RDFProfile):
    '''
    A custom implementation of DCAT-AP.de for OpenData.HRO, the open data portal of the municipality of Rostock

    It requires the European DCAT-AP profile (`euro_dcat_ap`)
    '''

    def __init__(self, graph, compatibility_mode=False):
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)

        with open(os.path.join(dir_path, "mappings", "categories.json")) as json_data:
            self.category_mapping = json.load(json_data)

        with open(os.path.join(dir_path, "mappings", "coverages.json")) as json_data:
            self.coverage_mapping = json.load(json_data)

        with open(os.path.join(dir_path, "mappings", "formats.json")) as json_data:
            self.format_mapping = json.load(json_data)

        with open(os.path.join(dir_path, "mappings", "licenses.json")) as json_data:
            self.license_mapping = json.load(json_data)

        super(DCATAPdeHROProfile, self).__init__(graph, compatibility_mode)

    def parse_dataset(self, dataset_dict, dataset_ref):

        # We're not interested in parsing RDF datasets at the moment

        return dataset_dict

    def graph_from_dataset(self, dataset_dict, dataset_ref):

        g = self.g

        dist_additons = {}

        # bind namespaces to have readable names in RDF Document
        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)

        # Nr. 40 - Contributor
        contributorId = pylons.config.get('ckanext.hro_dcatapde.contributorid')
        if contributorId:
            g.add( (dataset_ref, DCATDE.contributorID, Literal(contributorId) ))

        # Nr. 41 - Contact Point
        # If a maintainer name is given, set this to be the name of the 
        # contact point. If not, use name of author/VÖ Stelle (ckanext-dcat default).
        for contactPoint_ref in g.objects(dataset_ref, DCAT.contactPoint):
            for email in g.objects(contactPoint_ref, VCARD.hasEmail):
                g.remove( (contactPoint_ref, VCARD.hasEmail, Literal(email)) )
                g.add( (contactPoint_ref, VCARD.hasEmail, URIRef("mailto:" + email)) )

        # Nr. 44 - Publisher
        publisher_ref = BNode()
        publisher_name = self._get_dataset_value(dataset_dict, 'author')
        publisher_url = self._get_dataset_value(dataset_dict, 'url')
        g.add( (publisher_ref, RDF.type, FOAF.Organization) )
        g.add( (publisher_ref, FOAF.name, Literal(publisher_name)) )
        if publisher_url:
            g.add( (publisher_ref, FOAF.homepage, URIRef(publisher_url)) )
        g.add( (dataset_ref, DCT.publisher, publisher_ref) )

        # Nr. 45 - Kategorie
        groups = self._get_dataset_value(dataset_dict, 'groups')
        for group in groups:
            dcat_groups = self.category_mapping[group['name']]
            if dcat_groups is not None:
                for dcat_group in dcat_groups:
                    g.add( (dataset_ref, DCAT.theme, MDRTHEME[dcat_group]) )
                    # MDRTHEME.xyz is not dereferencable, so we add some additional
                    # triples that link to the downloadable source:
                    g.add( (MDRTHEME[dcat_group], RDFS.isDefinedBy, URIRef(MDRTHEME)) )
                    g.add( (URIRef(MDRTHEME), RDFS.seeAlso, URIRef("http://publications.europa.eu/mdr/resource/authority/data-theme/skos-ap-eu/data-theme-skos-ap-act.rdf")) )



        # Nr. 48 - conformsTo (Application Profile der Metadaten)
        g.add( (dataset_ref, DCT.conformsTo, URIRef(DCATDE)) )

        # Nr. 49 - 52 (Urheber, Verwalter, Bearbeiter, Autor) - we don't know this

        # Nr. 59 - Sprache
        g.add( (dataset_ref, DCT.language, MDRLANG.DEU) )
        # MDRLANG.DEU is not dereferencable, so we add some additional
        # triples that link to the downloadable source:
        g.add( (MDRLANG.DEU, RDFS.isDefinedBy, URIRef(MDRLANG)) )
        g.add( (URIRef(MDRLANG), RDFS.seeAlso, URIRef("http://publications.europa.eu/mdr/resource/authority/language/skos-ap-eu/languages-skos-ap-act.rdf")) )

        # Nr. 61 - Provenienz

        # TODO: geharvestete Datensätze kennzeichnen?

        # Nr. 66 - dct:spatial via geonames reference
        # Nr. 72 - dcatde:politicalGeocodingLevelURI
        # Nr. 73 - dcatde:politicalGeocodingURI
        # passt leider nur bedingt auf Berlin (nur federal, state, administrativeDistrict)

        geographical_coverage = self._get_dataset_value(dataset_dict, 'geographical_coverage')
        if geographical_coverage in self.coverage_mapping:
            coverage_object = self.coverage_mapping[geographical_coverage]
            if 'geonames' in coverage_object:
                g.add( (dataset_ref, DCT.spatial, URIRef(coverage_object['geonames'])) )
            if 'politicalGeocodingURI' in coverage_object:
                g.add( (dataset_ref, DCATDE.politicalGeocodingURI, URIRef(coverage_object['politicalGeocodingURI'])) )
            if 'politicalGeocodingLevelURI' in coverage_object:
                g.add( (dataset_ref, DCATDE.politicalGeocodingLevelURI, URIRef(coverage_object['politicalGeocodingLevelURI'])) )



        # Enhance Distributions
        ## License
        if 'license_id' in dataset_dict:
            ogd_license_code = dataset_dict['license_id']
            if ogd_license_code in self.license_mapping:
                dist_additons['license_id'] = self.license_mapping[ogd_license_code]['dcatde-id']

        ## Attribution Text
        if 'attribution_text' in dataset_dict:
            dist_additons['attribution_text'] = dataset_dict.get('attribution_text')

        for resource_dict in dataset_dict.get('resources', []):
            for distribution in g.objects(dataset_ref, DCAT.distribution):
                # Match distribution in graph and resource in ckan-dict
                if unicode(distribution) == resource_uri(resource_dict):
                    self.enhance_distribution_resource(g, distribution, resource_dict, dist_additons)

    def enhance_distribution_resource(self, g, distribution_ref, resource_dict, dist_additons):

        # Nr. 77 - License (derived from dataset license)
        if 'license_id' in dist_additons:
            g.add( (distribution_ref, DCT.license, DCATDE_LIC[dist_additons['license_id']]) )

        # Nr. 78 - Format
        for format_string in g.objects(distribution_ref, DCT['format']):
            g.remove( (distribution_ref, DCT['format'], Literal(format_string)) )
            format_string = format_string.toPython()
            if format_string in self.format_mapping:
                format_uri = self.format_mapping[format_string]['uri']
                g.add( (distribution_ref, DCT['format'], URIRef(format_uri)) )

        # Nr. 93 - dcatde:licenseAttributionByText
        if 'attribution_text' in dist_additons:
            g.add( (distribution_ref, DCATDE.licenseAttributionByText, Literal(dist_additons['attribution_text'])) )       

