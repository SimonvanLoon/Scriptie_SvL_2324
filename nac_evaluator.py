import pandas as pd
import json
import math
import re

# ----------------------------
# Helpers
# ----------------------------
def parse_set(value):
    if not value or not isinstance(value, str):
        return set()
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return set(parsed)
    except Exception:
        return {value}
    return set()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def compare_point(ai_lat, ai_lon, gold_lat, gold_lon, tol_m=5000):
    try:
        ai_lat, ai_lon = float(ai_lat), float(ai_lon)
        gold_lat, gold_lon = float(gold_lat), float(gold_lon)
    except ValueError:
        return False, None
    dist = haversine(ai_lat, ai_lon, gold_lat, gold_lon)
    return dist <= tol_m, dist

def field_matches(ai_val, gold_val, col):
    if col in ("feature_class", "feature_code"):
        gold_set = {str(gold_val).strip()} if pd.notna(gold_val) else set()
    else:
        gold_set = parse_set(gold_val)
    return (not ai_val and not gold_set) or (ai_val in gold_set)

def get_row_index(key):
    match = re.search(r'_(\d+)$', key)
    if match:
        return int(match.group(1))
    return None

# ----------------------------
# Evaluation
# ----------------------------
def evaluate_json(ai_json, enriched_df, label=""):
    total_fields = 0
    correct_fields = 0
    nac_total = 0
    nac_correct = 0
    geoname_total = 0
    geoname_correct = 0
    coord_total = 0
    coord_correct = 0

    print(f"\n=== Evaluating against {label} corpus ===")

    # ----------------------------
    # NEW: extract articles from new run format
    # ----------------------------
    articles = ai_json.get("articles", {})

    for file_id, article_obj in articles.items():
        print(f"\n--- Article {file_id} ---")

        # Skip invalid JSON outputs
        if not article_obj.get("valid_json", False):
            print("⚠️ Skipping article — invalid JSON output")
            continue

        toponyms = article_obj.get("llm_response_parsed", {})
        if not isinstance(toponyms, dict):
            print("⚠️ Skipping article — parsed output is not a dict")
            continue

        gold_rows = enriched_df[
            enriched_df["file_id"].astype(str).str.strip() == str(file_id).strip()
        ].reset_index(drop=True)

        if gold_rows.empty:
            print(f"⚠️ No gold annotations found for article {file_id}")
            continue

        for key, ai_entry in toponyms.items():
            print(f"\n{key} = {{")

            row_idx = get_row_index(key)
            if row_idx is None:
                print(f"  ⚠️ Could not parse row index from key '{key}', skipping.")
                continue

            tsv_pos = row_idx - 1
            if tsv_pos >= len(gold_rows):
                print(f"  ⚠️ Row index {row_idx} out of range "
                      f"(article has {len(gold_rows)} gold rows), skipping.")
                continue

            gold_row = gold_rows.iloc[tsv_pos]

            fields = [
                ("Country",      "Country_names"),
                ("ADM1",         "ADM1_names"),
                ("ADM2",         "ADM2_names"),
                ("ADM3",         "ADM3_names"),
                ("ADM4",         "ADM4_names"),
                ("FeatureClass", "feature_class"),
                ("FeatureCode",  "feature_code"),
            ]

            nac_match_all = True
            for field, col in fields:
                ai_val = ai_entry.get(field, "")
                total_fields += 1
                if field_matches(ai_val, gold_row[col], col):
                    print(f'    "{field}": "{ai_val}"  ✅')
                    correct_fields += 1
                else:
                    print(f'    "{field}": "{ai_val}"  ❌')
                    if field != "FeatureCode":
                        nac_match_all = False

            nac_total += 1
            if nac_match_all:
                print('    "NAC_address": CORRECT ✅')
                nac_correct += 1
            else:
                print('    "NAC_address": INCORRECT ❌')

            geoname_total += 1
            ai_gid = ai_entry.get("GeoNameID", "")
            if ai_gid == gold_row["geonameid"]:
                print(f'    "GeoNameID": "{ai_gid}"  ✅')
                geoname_correct += 1
            else:
                print(f'    "GeoNameID": "{ai_gid}"  ❌')

            coord_total += 1
            ai_lat = ai_entry.get("Latitude", "")
            ai_lon = ai_entry.get("Longitude", "")
            gold_lat = gold_row.get("latitude", "")
            gold_lon = gold_row.get("longitude", "")
            ok, dist = compare_point(ai_lat, ai_lon, gold_lat, gold_lon)
            if ok:
                print(f'    "Coordinates": ({ai_lat}, {ai_lon})  ✅ distance={dist:.1f} m')
                coord_correct += 1
            elif dist is not None:
                print(f'    "Coordinates": ({ai_lat}, {ai_lon})  ❌ distance={dist:.1f} m')
            else:
                print(f'    "Coordinates": ({ai_lat}, {ai_lon})  ❌ (invalid values)')

            print("}")

    field_acc = correct_fields / total_fields if total_fields else 0
    nac_acc   = nac_correct   / nac_total     if nac_total     else 0
    gid_acc   = geoname_correct / geoname_total if geoname_total else 0
    coord_acc = coord_correct / coord_total   if coord_total   else 0

    print(f"\n=== Overall Field Accuracy ({label}): {field_acc:.2%} ===")
    print(f"=== NAC Address Accuracy ({label}): {nac_acc:.2%} ===")
    print(f"=== GeoNames ID Accuracy ({label}): {gid_acc:.2%} ===")
    print(f"=== Coordinate Accuracy@5km ({label}): {coord_acc:.2%} ===")

    return field_acc, nac_acc, gid_acc, coord_acc

# ----------------------------
# Main
# ----------------------------
def main():
    cols = [
        "file_id", "toponym", "geonameid", "in_title",
        "name", "asciiname", "alternatenames", "latitude", "longitude",
        "feature_class", "feature_code", "country_code", "cc2",
        "admin1_code", "admin2_code", "admin3_code", "admin4_code",
        "population", "elevation", "dem", "timezone", "modification_date",
        "Country_names", "ADM1_names", "ADM2_names", "ADM3_names", "ADM4_names"
    ]

    lgl_enriched = pd.read_csv("lgl_annotations_enriched.tsv", sep="\t", dtype=str, names=cols, header=None)
    dna_enriched = pd.read_csv("dna_annotations_enriched.tsv", sep="\t", dtype=str, names=cols, header=None)

    with open("outputs/Extensive_DNA_strict_v2/run_20260608_200958.json", "r", encoding="utf-8") as f:
        ai_json = json.load(f)

    evaluate_json(ai_json, lgl_enriched, label="LGL")
    evaluate_json(ai_json, dna_enriched, label="DNA")

if __name__ == "__main__":
    main()
