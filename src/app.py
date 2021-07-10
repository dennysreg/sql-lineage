from mo_sql_parsing import parse
import json
import pprint

def translate(p):
    cte = p['with'][0]
    fqn = [f"{cte['value']['from']}.{item['value']}" for item in cte['value']['select']]
    print(fqn)


if __name__ == '__main__':
    filename = 'query/aggregation.sql'
    with open(filename) as f:
        query = f.read()
    p = parse(query)
    translate(p)