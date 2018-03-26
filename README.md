# Extension for *CKAN*: HRO DCAT-AP.de

A custom implementation of [DCAT-AP.de](http://dcat-ap.de) for OpenData.HRO, the open data portal of the municipality of Rostockk – view it in production: https://www.opendata-hro.de

*HRO DCAT-AP.de* draws heavily on [*ckanext-dcatde*](https://github.com/GovDataOfficial/ckanext-dcatde) but keeps the core CKAN schema, i.e. no database conversions necessary. Many thanks to the contributors to [*ckanext-dcatde_berlin*](https://github.com/berlinonline/ckanext-dcatde_berlin) where much of the code is derived from.

## Requirements

*   [*CKAN*](https://github.com/ckan/ckan) >= 2.7.0
*   [*ckanext-dcat*](https://github.com/ckan/ckanext-dcat) >= 0.0.7

## Installation

To install ckanext-hro_dcatapde for production:

1.  Activate your *CKAN* virtual *Python* environment, for example:

        . /usr/lib/ckan/default/bin/activate

1.  Install the ckanext-hro_dcatapde *Python* package into your virtual *Python* environment:

        pip install ckanext-hro_dcatapde

1.  Add `hro_dcatapde` to the `ckan.plugins` setting in your *CKAN* config file (by default the config file is located at `/etc/ckan/default/production.ini`)
1.  Add the following lines to your *CKAN* config file:

        ckanext.dcat.enable_content_negotiation = True
        ckanext.dcat.rdf.profiles = euro_dcat_ap dcatap_de
        ckanext.dcatde.contributorid = [your contributor id]

1.  Restart *CKAN*. For example, if you have deployed *CKAN* with *Apache HTTP Server* on *Ubuntu*:

        sudo service apache2 reload

## Development installation

To install ckanext-hro_dcatapde for development, activate your *CKAN* virtualenv and do:

    git clone https://github.com/kvlahrosch/ckanext-hro_dcatapde.git
    cd ckanext-hro_dcatapde
    python setup.py develop
    pip install -r dev-requirements.txt
