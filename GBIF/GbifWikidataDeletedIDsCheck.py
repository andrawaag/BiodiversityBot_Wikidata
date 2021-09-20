import pandas
from wikidataintegrator import wdi_core
import requests

query = """
SELECT * WHERE {
   ?item wdt:P846 ?gbifTaxonId .
}
"""
dataWikidata = wdi_core.WDFunctionsEngine.execute_sparql_query(query=query, as_dataframe=True)
dataGBIF = pandas.read_csv("http://download.gbif.org/custom_download/mgrosjean/deleted_taxa_gbif_backbone.csv", delimiter='\t')

result=dataWikidata.assign(gbifIDcheck=dataWikidata.gbifTaxonId.isin(dataGBIF.taxon_key).astype(int))

deletedIDs = result['gbifIDcheck'].value_counts()[1]
print("GBIF species ID that are deleted but linked on wikidata:", deletedIDs)
print(result)
print(dataWikidata)
