import pytest

from app.engine.tarot import DECK_SIZE, MAX_CARDS, draw_cards, get_card, load_deck


def test_deck_has_78_unique_cards():
    deck = load_deck()
    assert len(deck) == DECK_SIZE
    assert set(deck) == set(range(1, DECK_SIZE + 1))


def test_deck_composition():
    cards = load_deck().values()
    assert sum(card["arcana"] == "major" for card in cards) == 22
    for suit in ("wands", "cups", "swords", "pentacles"):
        assert sum(card["suit"] == suit for card in cards) == 14


def test_every_card_has_meanings():
    for card in load_deck().values():
        assert card["name_vi"] and card["name_en"]
        assert len(card["upright"]) >= 2
        assert len(card["reversed"]) >= 2


def test_sensitive_cards_have_safety_note():
    cards_by_name = {card["name_en"]: card for card in load_deck().values()}
    assert "safety_note" in cards_by_name["Death"]
    assert "safety_note" in cards_by_name["The Tower"]


def test_same_seed_same_result():
    assert draw_cards(3, seed=42) == draw_cards(3, seed=42)


def test_seed_zero_is_respected():
    assert draw_cards(3, seed=0) == draw_cards(3, seed=0)
    assert draw_cards(3, seed=0)["seed"] == 0


def test_different_seeds_usually_differ():
    results = {
        tuple(card["card_id"] for card in draw_cards(3, seed=seed)["cards"])
        for seed in range(20)
    }
    assert len(results) > 1


def test_no_duplicate_cards_in_one_draw():
    for seed in range(50):
        ids = [card["card_id"] for card in draw_cards(MAX_CARDS, seed=seed)["cards"]]
        assert len(set(ids)) == len(ids)
        assert all(1 <= card_id <= DECK_SIZE for card_id in ids)


def test_auto_seed_can_replay():
    first = draw_cards(5)
    replay = draw_cards(5, seed=first["seed"])
    assert first == replay


def test_reversed_is_boolean_and_both_occur():
    flags = [
        card["is_reversed"]
        for seed in range(30)
        for card in draw_cards(5, seed=seed)["cards"]
    ]
    assert all(isinstance(flag, bool) for flag in flags)
    assert True in flags and False in flags


def test_invalid_count_rejected():
    for bad_count in (0, -1, MAX_CARDS + 1):
        with pytest.raises(ValueError):
            draw_cards(bad_count)


def test_get_card_unknown_id():
    assert get_card(1)["name_en"] == "The Fool"
    with pytest.raises(ValueError):
        get_card(999)
