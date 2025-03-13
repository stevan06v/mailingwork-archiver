import json
from datetime import datetime
from operator import itemgetter

DATA_FILE="data/output.json"

def read_json():
    with open(DATA_FILE) as f:
        data = json.load(f)
        if data is None:
            raise Exception("No data")
        return data

def refine_data(data):
    valid_entries = list()

    for iterator in data:
        if iterator.get("date", ""):
            valid_entries.append(iterator)

    return valid_entries


def sort_by_date(data):
    parsed_entries = []
    filtered_entries = list()

    for entry in data:
        if isinstance(entry.get("date"), str):
            try:
                entry["date"] = datetime.strptime(entry["date"], "%d.%m.%Y")
            except ValueError as e:
                print(f"Error parsing date: {entry['date']} - {e}")
                continue
        elif isinstance(entry.get("date"), datetime):
            pass

        parsed_entries.append(entry)


    sorted_data = sorted(parsed_entries, key=itemgetter('date'), reverse=True)

    for iterator, entry in enumerate(sorted_data):
        if iterator %  2 == 0:
            continue
        filtered_entries.append(entry)

    print(filtered_entries)
    print(len(filtered_entries))

    return filtered_entries

