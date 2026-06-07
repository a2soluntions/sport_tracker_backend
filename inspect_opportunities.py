from database_connector import banco_de_dados

try:
    resp = banco_de_dados.table('ev_opportunities').select('*').execute()
    print("Opportunities count:", len(resp.data))
    if len(resp.data) > 0:
        print("First opportunity:")
        print(resp.data[0])
    else:
        print("No opportunities found.")
except Exception as e:
    print("Error querying database:", e)
