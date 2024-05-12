import json

with open('/content/webdo_articles.json', 'r', encoding='utf-8') as file:
    data_webdo = json.load(file)

with open('/content/nessma_articles.json', 'r', encoding='utf-8') as file:
    data_nessma = json.load(file)

with open('/content/kapitalis_articles.json', 'r', encoding='utf-8') as file:
    data_kapitalis = json.load(file)

with open('/content/jawharafm_articles.json', 'r', encoding='utf-8') as file:
    data_jawhara = json.load(file)

with open('/content/ifm_articles.json', 'r', encoding='utf-8') as file:
    data_ifm = json.load(file)

# Concatenate JSON objects into a list
json_array = []

json_array.extend(data_webdo)
json_array.extend(data_nessma)
json_array.extend(data_kapitalis)
json_array.extend(data_jawhara)
json_array.extend(data_ifm)


# Convert list of JSON objects to JSON array
concatenated_json = json.dumps(json_array, ensure_ascii=False)
file_name = "concatenated_articles.json"
# Write the JSON data to the file
with open(file_name, "w", encoding="utf-8") as json_file:
      json_file.write(concatenated_json)

print(concatenated_json)