from deduplication.deduplicator import ListingDeduplicator
from normalizers.vehicle_normalizer import VehicleNormalizer


def test_deduplicate_by_url():
    n = VehicleNormalizer()
    rows = [
        n.normalize({"marca": "Honda", "modelo": "Civic", "ano": 2020, "preco": 110000, "estado": "SP", "url": "x"}),
        n.normalize({"marca": "Honda", "modelo": "Civic", "ano": 2020, "preco": 110500, "estado": "SP", "url": "x"}),
    ]
    result = ListingDeduplicator().deduplicate(rows)
    assert len(result.clean_records) == 1
    assert len(result.duplicates) == 1
