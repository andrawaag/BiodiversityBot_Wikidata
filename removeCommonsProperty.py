from wikidataintegrator import wdi_core, wdi_login
import os
import pprint

if "WDUSER" in os.environ and "WDPASS" in os.environ:
    WDUSER = os.environ['WDUSER']
    WDPASS = os.environ['WDPASS']
else:
    raise ValueError("WDUSER and WDPASS must be specified in local.py or as environment variables")

login = wdi_login.WDLogin(WDUSER, WDPASS)

query = """
SELECT * WHERE {
  ?item wdt:P31 wd:Q16521 .
  ?item wdt:P4765 ?url .
  ?item p:P4765 ?node .
  ?node prov:wasDerivedFrom ?reference .
  ?reference pr:P248 wd:Q16958215 .
}
"""

results = wdi_core.WDItemEngine.execute_sparql_query(query=query)
pprint.pprint(results)

counter = 0
for wd in results["results"]["bindings"]:
    qid = wd["item"]["value"].replace("http://www.wikidata.org/entity/", "")
    data2add = [wdi_core.WDBaseDataType.delete_statement(prop_nr='P4765')]
    counter += 1

    try:
        wdPage = wdi_core.WDItemEngine(qid, data=data2add)
        print(counter, wdPage.write(login))
    except:
        pass