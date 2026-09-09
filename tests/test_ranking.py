from app.services.ranking import reciprocal_rank_fusion


def test_rrf_rewards_items_found_by_both_retrievers() -> None:
    vector = [("a", "A"), ("b", "B")]
    keyword = [("b", "B"), ("c", "C")]

    result = reciprocal_rank_fusion([vector, keyword])

    assert result[0].key == "b"
    assert {item.key for item in result} == {"a", "b", "c"}


def test_rrf_respects_limit() -> None:
    result = reciprocal_rank_fusion([[('a', 'A'), ('b', 'B')]], limit=1)

    assert [item.key for item in result] == ["a"]

