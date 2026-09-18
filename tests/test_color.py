from fcf.qa.color import delta_e76, hex_to_rgb, srgb_to_lab


def test_same_colour_delta_zero():
    c = (27, 42, 65)
    assert delta_e76(c, c) == 0


def test_hex_roundtrip_lab_finite():
    lab = srgb_to_lab(hex_to_rgb("#1B2A41"))
    assert all(isinstance(x, float) for x in lab)
