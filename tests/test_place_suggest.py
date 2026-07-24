from fuel.services.place_suggest import PlaceSuggestIndex, reset_place_suggest_cache


def test_st_louis_matches_saint_louis(tmp_path):
    csv_path = tmp_path / "cities.csv"
    csv_path.write_text(
        "city,state,latitude,longitude\n"
        "Saint Louis,MO,38.6,-90.2\n"
        "East Saint Louis,IL,38.6,-90.1\n"
        "Louisville,KY,38.2,-85.7\n"
        "West Louisville,KY,37.7,-87.3\n"
        "Dallas,TX,32.7,-96.7\n"
        "St Charles,MO,38.7,-90.5\n",
        encoding="utf-8",
    )
    index = PlaceSuggestIndex.from_csv(csv_path)

    for query in ("St. Louis", "st louis", "Saint Louis", "st. lou"):
        hits = index.suggest(query, limit=5)
        assert hits, f"expected hits for {query!r}"
        assert hits[0].city == "St. Louis", hits
        assert hits[0].state == "MO", hits
        assert hits[0].label == "St. Louis, MO", hits


def test_suggest_does_not_return_unrelated_cities(tmp_path):
    csv_path = tmp_path / "cities.csv"
    csv_path.write_text(
        "city,state,latitude,longitude\n"
        "Saint Louis,MO,38.6,-90.2\n"
        "West Louisville,KY,37.7,-87.3\n"
        "Dallas,TX,32.7,-96.7\n",
        encoding="utf-8",
    )
    index = PlaceSuggestIndex.from_csv(csv_path)
    labels = [h.label for h in index.suggest("St. Louis", limit=8)]
    assert labels[0] == "St. Louis, MO"
    assert "Dallas, TX" not in labels
    assert "West Louisville, KY" not in labels


def test_new_york_and_fort_worth_aliases(tmp_path):
    csv_path = tmp_path / "cities.csv"
    csv_path.write_text(
        "city,state,latitude,longitude\n"
        "New York,NY,40.7,-74.0\n"
        "Fort Worth,TX,32.7,-97.3\n",
        encoding="utf-8",
    )
    index = PlaceSuggestIndex.from_csv(csv_path)
    assert index.suggest("new y", limit=3)[0].label == "New York, NY"
    assert index.suggest("ft worth", limit=3)[0].label.startswith("Ft. Worth")


def test_east_saint_louis_in_results(tmp_path):
    csv_path = tmp_path / "cities.csv"
    csv_path.write_text(
        "city,state,latitude,longitude\n"
        "Saint Louis,MO,38.6,-90.2\n"
        "East Saint Louis,IL,38.6,-90.1\n"
        "Lake Saint Louis,MO,38.8,-90.7\n",
        encoding="utf-8",
    )
    index = PlaceSuggestIndex.from_csv(csv_path)
    labels = [h.label for h in index.suggest("st louis", limit=12)]
    assert "St. Louis, MO" in labels
    assert "East St. Louis, IL" in labels
    assert "Lake St. Louis, MO" in labels


def test_reset_cache_helper():
    reset_place_suggest_cache()
