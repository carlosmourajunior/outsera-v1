from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_movies_default_pagination(client: TestClient) -> None:
    response = client.get("/movies")
    assert response.status_code == 200

    body = response.json()
    assert body["page"] == 1
    assert body["size"] == 50
    assert body["total"] == 6
    assert len(body["items"]) == 6


def test_list_movies_filter_by_year(client: TestClient) -> None:
    response = client.get("/movies", params={"year": 1980})
    body = response.json()

    assert body["total"] == 2
    assert {item["title"] for item in body["items"]} == {
        "Can't Stop the Music",
        "Cruising",
    }


def test_list_movies_filter_by_winner(client: TestClient) -> None:
    response = client.get("/movies", params={"winner": True})
    body = response.json()

    assert body["total"] == 4
    assert all(item["winner"] for item in body["items"])


def test_list_movies_combined_filters(client: TestClient) -> None:
    response = client.get("/movies", params={"year": 1980, "winner": False})
    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "Cruising"


def test_list_movies_pagination_slices_results(client: TestClient) -> None:
    response = client.get("/movies", params={"page": 2, "size": 2})
    body = response.json()

    assert body["page"] == 2
    assert body["size"] == 2
    assert body["total"] == 6
    assert [item["title"] for item in body["items"]] == [
        "Bonfire of the Vanities",
        "Battlefield Earth",
    ]


def test_list_movies_item_shape(client: TestClient) -> None:
    response = client.get("/movies", params={"year": 1980, "winner": False})
    item = response.json()["items"][0]

    assert item["title"] == "Cruising"
    assert item["studios"] == ["Lorimar Productions", "United Artists"]
    assert item["producers"] == ["Jerry Weintraub", "Bob Cavallo"]
    assert item["winner"] is False
    assert isinstance(item["id"], int)


def test_list_movies_rejects_page_below_one(client: TestClient) -> None:
    assert client.get("/movies", params={"page": 0}).status_code == 422


def test_list_movies_rejects_size_above_maximum(client: TestClient) -> None:
    assert client.get("/movies", params={"size": 101}).status_code == 422


def test_list_movies_rejects_size_below_one(client: TestClient) -> None:
    assert client.get("/movies", params={"size": 0}).status_code == 422


def test_get_movie_found(client: TestClient) -> None:
    response = client.get("/movies/1")
    assert response.status_code == 200

    body = response.json()
    assert body["title"] == "Can't Stop the Music"
    assert body["producers"] == ["Allan Carr"]
    assert body["winner"] is True


def test_get_movie_not_found(client: TestClient) -> None:
    response = client.get("/movies/9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Filme nao encontrado"}


def test_award_intervals_shape_and_camel_case_aliases(client: TestClient) -> None:
    response = client.get("/producers/intervals")
    assert response.status_code == 200

    body = response.json()
    assert set(body.keys()) == {"min", "max"}
    for bucket in (body["min"], body["max"]):
        for entry in bucket:
            assert set(entry.keys()) == {
                "producer",
                "interval",
                "previousWin",
                "followingWin",
            }


def test_award_intervals_computed_values(client: TestClient) -> None:
    # No dataset de teste, Peter Guber e Jon Peters sao os unicos produtores com
    # duas vitorias (1990 e 2015): interval 25, empatado no minimo e no maximo,
    # ordenado por producer no empate ("Jon Peters" antes de "Peter Guber").
    response = client.get("/producers/intervals")
    body = response.json()

    expected = [
        {
            "producer": "Jon Peters",
            "interval": 25,
            "previousWin": 1990,
            "followingWin": 2015,
        },
        {
            "producer": "Peter Guber",
            "interval": 25,
            "previousWin": 1990,
            "followingWin": 2015,
        },
    ]
    assert body["min"] == expected
    assert body["max"] == expected
