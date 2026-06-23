from ssnet.config import load_config


def test_load_config_reads_buckets(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(
        'site_title = "x"\nbase_url = "https://x"\n'
        '[aws]\nsite_bucket = "b"\nimages_bucket = "i"\nprofile = "ssnet"\n'
    )
    cfg = load_config(p)
    assert cfg["site_title"] == "x"
    assert cfg["aws"]["site_bucket"] == "b"
