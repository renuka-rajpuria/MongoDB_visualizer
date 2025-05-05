import streamlit as st
from pymongo import MongoClient
import pandas as pd
from bson import ObjectId
import json

def flatten_dict(d, parent_key='', sep='.'):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        elif isinstance(v, list):
            if all(isinstance(i, dict) for i in v):  # List of dicts
                for idx, item in enumerate(v):
                    items.update(flatten_dict(item, f"{new_key}[{idx}]", sep=sep))
            else:
                items[new_key] = str(v)  # store as string
        else:
            items[new_key] = v
    return items


def unflatten_dict(d, sep='.'):
    result_dict = {}
    for key, value in d.items():
        parts = key.split(sep)
        d_ref = result_dict
        for part in parts[:-1]:
            if part not in d_ref or not isinstance(d_ref[part], dict):
                d_ref[part] = {}
            d_ref = d_ref[part]
        d_ref[parts[-1]] = value
    return result_dict

st.title("MongoDB Visual Editor")

uri = st.text_input("Mongo URI", type="password")
if uri:
    try:
        client = MongoClient(uri)
        db_names = client.list_database_names()
        db_name = st.selectbox("Select Database", db_names)
        if db_name:
            db = client[db_name]
            col_names = db.list_collection_names()
            col_name = st.selectbox("Select Collection", col_names)
            collection = db[col_name]

            docs = list(collection.find())
            ids = [str(doc["_id"]) for doc in docs]
            flat_docs = [flatten_dict({**doc, "_id": str(doc["_id"])}) for doc in docs]

            df = pd.DataFrame(flat_docs)
            st.subheader("Edit Documents")
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

            if st.button("Save Changes"):
                collection.delete_many({})
                for doc in edited_df.to_dict(orient='records'):
                    doc = unflatten_dict(doc)
                    doc["_id"] = ObjectId(doc["_id"])  # preserve original ID
                    collection.insert_one(doc)
                st.success("Changes saved!")

    except Exception as e:
        st.error(f"Connection failed: {e}")
