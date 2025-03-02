import requests

# Get user input
SOURCE_METABASE_URL = input("Enter the source Metabase URL: ").strip()
TARGET_METABASE_URL = input("Enter the target Metabase URL: ").strip()

SOURCE_SESSION_TOKEN = input("Enter the source session token: ").strip()
TARGET_SESSION_TOKEN = input("Enter the target session token: ").strip()

COLLECTION_ID = input("Enter the collection ID to transfer: ").strip()
NEW_COLLECTION_NAME = input("Enter the new collection name: ").strip()

# Set headers
headers = {"X-Metabase-Session": SOURCE_SESSION_TOKEN}
target_headers = {"X-Metabase-Session": TARGET_SESSION_TOKEN, "Content-Type": "application/json"}

# Fetch collection details
collection_url = f"{SOURCE_METABASE_URL}/api/collection/{COLLECTION_ID}"
response = requests.get(collection_url, headers=headers)

if response.status_code == 200:
    collection_data = response.json()

    new_collection_data = {
        "name": NEW_COLLECTION_NAME,
        "description": collection_data.get("description", ""),
        "parent_id": None,
        "can_delete": collection_data.get("can_delete", False),
    }

    # Create new collection in target Metabase
    create_collection_url = f"{TARGET_METABASE_URL}/api/collection"
    response = requests.post(create_collection_url, json=new_collection_data, headers=target_headers)

    if response.status_code == 200:
        new_collection = response.json()
        NEW_COLLECTION_ID = new_collection["id"]
        print(f"✅ Collection '{new_collection['name']}' created! ID: {NEW_COLLECTION_ID}")

        # **Step 1: Transfer Cards (Questions)**
        cards_url = f"{SOURCE_METABASE_URL}/api/collection/{COLLECTION_ID}/items"
        response = requests.get(cards_url, headers=headers)

        old_card_to_new_card_map = {}

        if response.status_code == 200:
            cards = response.json().get("data", [])
            print(f"🔹 {len(cards)} cards found, transferring...")

            for card in cards:
                card_id = card.get("id")
                if not card_id:
                    print("❌ Invalid card data:", card)
                    continue

                card_details_url = f"{SOURCE_METABASE_URL}/api/card/{card_id}"
                response = requests.get(card_details_url, headers=headers)

                if response.status_code == 200:
                    card_details = response.json()
                    new_card_data = {
                        "name": card_details["name"],
                        "description": card_details.get("description", ""),
                        "dataset_query": card_details["dataset_query"],
                        "visualization_settings": card_details["visualization_settings"],
                        "display": card_details.get("display", "table"),
                        "collection_id": NEW_COLLECTION_ID,
                    }

                    create_card_url = f"{TARGET_METABASE_URL}/api/card"
                    response = requests.post(create_card_url, json=new_card_data, headers=target_headers)

                    if response.status_code == 200:
                        new_card = response.json()
                        old_card_to_new_card_map[card_id] = new_card["id"]
                        print(f"✅ Card '{card_details['name']}' transferred!")
                    else:
                        print(f"❌ Failed to transfer card '{card_details['name']}'! Error: {response.text}")
                else:
                    print(f"❌ Failed to fetch card details for ID {card_id}!")

        # **Step 2: Transfer Dashboards with Cards & Filters**
        dashboards_url = f"{SOURCE_METABASE_URL}/api/dashboard"
        response = requests.get(dashboards_url, headers=headers)

        if response.status_code == 200:
            dashboards = response.json()
            dashboards_in_collection = [d for d in dashboards if d.get("collection_id") == int(COLLECTION_ID)]
            print(f"🔹 {len(dashboards_in_collection)} dashboards found, transferring...")

            for dashboard in dashboards_in_collection:
                dashboard_id = dashboard["id"]
                dashboard_details_url = f"{SOURCE_METABASE_URL}/api/dashboard/{dashboard_id}"
                response = requests.get(dashboard_details_url, headers=headers)

                if response.status_code == 200:
                    dashboard_details = response.json()
                    new_dashboard_data = {
                        "name": dashboard_details["name"],
                        "description": dashboard_details.get("description", ""),
                        "collection_id": NEW_COLLECTION_ID,
                        "parameters": dashboard_details.get("parameters", []),
                        "dashcards": [],
                        "width": dashboard_details.get("width", "full"),
                        "param_fields": dashboard_details.get("param_fields", {}),
                        "can_delete": True,
                        "param_values": dashboard_details.get("param_values", {}),
                    }
                    print(f"🔹 Transferring dashboard '{dashboard_details['name']}'...")

                    # **Step 3: Transfer Cards Inside the Dashboard**
                    for card in dashboard_details.get("dashcards", []):
                        original_card_id = card.get("card_id")
                        if original_card_id and original_card_id in old_card_to_new_card_map:
                            new_card_id = old_card_to_new_card_map[original_card_id]
                            card["card_id"] = new_card_id
                            card["parameter_mappings"] = card.get("parameter_mappings", [])
                            for param in card["parameter_mappings"]:
                                param["card_id"] = new_card_id
                            new_dashboard_data["dashcards"].append(card)

                    # **Step 4: Update Filters to Reference New Cards**
                    for param in new_dashboard_data["parameters"]:
                        if "card_id" in param and param["card_id"] in old_card_to_new_card_map:
                            param["card_id"] = old_card_to_new_card_map[param["card_id"]]

                        if "target" in param and "card_id" in param["target"]:
                            old_card_id = param["target"]["card_id"]
                            if old_card_id in old_card_to_new_card_map:
                                param["target"]["card_id"] = old_card_to_new_card_map[old_card_id]

                    # **Step 5: Create New Dashboard**
                    create_dashboard_url = f"{TARGET_METABASE_URL}/api/dashboard"
                    response = requests.post(create_dashboard_url, json=new_dashboard_data, headers=target_headers)

                    if response.status_code == 200:
                        new_dashboard = response.json()
                        print(f"✅ Dashboard '{dashboard_details['name']}' transferred successfully!")

                        # **Step 6: Move Dashboard Filters to New Dashboard**
                        dashboard_id_new = new_dashboard["id"]
                        filters_url = f"{TARGET_METABASE_URL}/api/dashboard/{dashboard_id_new}"
                        response = requests.put(filters_url, json={
                            "parameters": new_dashboard_data["parameters"],
                            "dashcards": new_dashboard_data["dashcards"],
                            "width": new_dashboard_data["width"],
                            "can_delete": new_dashboard_data["can_delete"],
                            "param_fields": dashboard_details["param_fields"],
                            "param_values": dashboard_details["param_values"],
                        }, headers=target_headers)

                        if response.status_code == 200:
                            print(f"✅ Filters successfully moved for '{dashboard_details['name']}'!")
                        else:
                            print(f"❌ Failed to transfer filters for '{dashboard_details['name']}'! Error: {response.text}")

                    else:
                        print(f"❌ Failed to transfer dashboard '{dashboard_details['name']}'! Error: {response.text}")

    else:
        print("❌ Failed to create new collection in target Metabase!")

else:
    print("❌ Failed to fetch source collection data!")
