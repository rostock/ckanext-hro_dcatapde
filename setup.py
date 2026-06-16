from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
  name="ckanext-hro_dcatapde",
  version="3.1.0",
  description="Custom DCAT-AP.de implementation for OpenData.HRO (Rostock)",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/rostock/ckanext-hro_dcatapde",
  author="Sebastian Gutzeit",
  author_email="sebastian.gutzeit@rostock.de",
  license="AGPL-3.0-or-later",
  python_requires=">=3.11",
  packages=find_packages(exclude=["contrib", "docs", "tests*"]),
  namespace_packages=["ckanext"],
  include_package_data=True,
  install_requires=[],
  entry_points={
    "ckan.plugins": [
      "hro_dcatapde=ckanext.hro_dcatapde.plugin:Hro_DcatapdePlugin",
    ],
    "ckan.rdf.profiles": [
      "dcatap_de=ckanext.hro_dcatapde.profile:DCATAPdeHROProfile",
    ],
    "babel.extractors": [
      "ckan=ckan.lib.extract:extract_ckan",
    ],
  },
)
