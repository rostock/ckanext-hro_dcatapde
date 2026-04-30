# Extension for *CKAN*: HRO-DCAT-AP.de

A custom [DCAT-AP.de](https://www.dcat-ap.de/) implementation for **OpenData.HRO**, the open data portal of the Hanseatic and University City of Rostock (https://www.opendata-hro.de/).

This extension provides a specific DCAT-AP profile built on top of `euro_dcat_ap3` from [ckanext-dcat](https://github.com/ckan/ckanext-dcat). It extends and adapts functionality from [ckanext-dcatde](https://github.com/GovDataOfficial/ckanext-dcatde) and [ckanext-dcatde_berlin](https://github.com/berlinonline/ckanext-dcatde_berlin), following a non-intrusive approach—no database migrations and no changes to *CKAN* core.

Many thanks to the contributors of these projects for their foundational work.

## Requirements

*   [*CKAN*](https://github.com/ckan/ckan)
*   [*ckanext-dcat*](https://github.com/ckan/ckanext-dcat)

## Installation

1.  Activate your *CKAN* virtual *Python* environment, for example:

        . /usr/lib/ckan/default/bin/activate

1.  Install *HRO-DCAT-AP.de* into your virtual *Python* environment, for example:

        cd /usr/lib/ckan/default/src
        git clone https://github.com/rostock/ckanext-hro_dcatapde.git
        cd ckanext-hro_dcatapde
        pip install -e .

1.  Enable *HRO-DCAT-AP.de* in your *CKAN* config file (by default the config file is located at `/etc/ckan/default/ckan.ini`):

        ckan.plugins = [...] hro_dcatapde [...]

1.  Add the following lines to your *CKAN* config file:

        ckanext.dcat.rdf.profiles = euro_dcat_ap3 dcatap_de
        ckanext.hro_dcatapde.contributorid = [your contributor id]

1.  Restart *CKAN*. For example, if you have deployed *CKAN* with *Apache HTTP Server* on *Ubuntu*, run:

        sudo service apache2 reload

## Upgrade

1.  Activate your *CKAN* virtual *Python* environment, for example:

        . /usr/lib/ckan/default/bin/activate

1.  Upgrade *HRO-DCAT-AP.de* within your virtual *Python* environment:

        pip install --upgrade -r https://github.com/rostock/ckanext-hro_dcatapde/raw/master/requirements.txt
        pip install --upgrade -e 'git+https://github.com/rostock/ckanext-hro_dcatapde.git#egg=ckanext-hro_dcatapde'

1.  Restart *CKAN*. For example, if you have deployed *CKAN* with *Apache HTTP Server* on *Ubuntu*:

        sudo service apache2 reload
