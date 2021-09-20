from wikidataintegrator import wdi_core, wdi_login
import os

print("Logging in...")
if "WDUSER" in os.environ and "WDPASS" in os.environ:
    WDUSER = os.environ['WDUSER']
    WDPASS = os.environ['WDPASS']
else:
    raise ValueError("WDUSER and WDPASS must be specified in local.py or as environment variables")

login = wdi_login.WDLogin(WDUSER, WDPASS)

gbifid = "1000007"
qid = "http://www.wikidata.org/entity/Q12622254"

item = wdi_core.WDItemEngine(wd_item_id=qid.replace("http://www.wikidata.org/entity/", ""))

updated_statements = []
for statement in item.original_statements:
    if statement.get_prop_nr() == "P846":
        if statement.get_value() == gbifid:
              statement.set_rank("deprecated")
    updated_statements.append(statement)
item_updated = wdi_core.WDItemEngine(wd_item_id=qid.replace("http://www.wikidata.org/entity/", ""), data=updated_statements)
item_updated.write(login)