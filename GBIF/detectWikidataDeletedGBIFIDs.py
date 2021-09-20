import pandas 


dataWikidata = pandas.read_csv("Wikidata_GBIF_speciesIDs.csv", delimiter=',')
dataGBIF = pandas.read_csv("deleted_taxa_gbif_backbone.csv", delimiter='\t')

result=dataWikidata.assign(gbifIDcheck=dataWikidata.gbifTaxonId.isin(dataGBIF.taxon_key).astype(int))

deletedIDs = result['gbifIDcheck'].value_counts()[1]
print("GBIF species ID that are deleted but linked on wikidata:", deletedIDs)
print(result)
