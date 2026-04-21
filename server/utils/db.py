import os
import json
import uuid

BASE_PATH = "datasets"

def init_table(table_name):
    os.makedirs(BASE_PATH, exist_ok=True)
    path = f"{BASE_PATH}/{table_name}.json"

    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)

    return path


def read_table(path):
    with open(path, "r") as f:
        return json.load(f)


def write_table(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def generate_id():
    return str(uuid.uuid4())

def db_utils(table, action, data=None):
    path = init_table(table)
    records = read_table(path)

    # CREATE
    if action == "add":
        if not data:
            raise ValueError("Data required")

        new_record = {
            "id": generate_id(),
            **data
        }

        records.append(new_record)
        write_table(path, records)
        return new_record

    # GET (by id or all)
    elif action == "get":
        if not data or "id" not in data:
            return records

        for r in records:
            if r["id"] == data["id"]:
                return r

        return {"error": "not found"}

    # SEARCH (filtered)
    elif action == "search":
        if not data:
            return records

        return [
            r for r in records
            if all(r.get(k) == v for k, v in data.items())
        ]

    # DELETE
    elif action == "delete":
        if not data or "id" not in data:
            raise ValueError("ID required")

        new_records = [r for r in records if r["id"] != data["id"]]

        if len(new_records) == len(records):
            return {"error": "not found"}

        write_table(path, new_records)
        return {"status": "deleted"}

    # UPDATE
    elif action == "update":
        if not data or "id" not in data:
            raise ValueError("ID required")

        for r in records:
            if r["id"] == data["id"]:
                r.update(data)
                write_table(path, records)
                return r

        return {"error": "not found"}

    else:
        raise ValueError("Invalid action")