from __future__ import annotations

from fcf.domain.enums import Severity
from fcf.qa.color import clipping_ratio, dominant_delta_e, has_watermark, palette_overlap
from fcf.qa.engine import QACheck


def _ratio(aspect: str) -> float:
    a, b = aspect.split(":")
    return int(a) / int(b)


def check_image(meta, path, product, brand, policy) -> list[QACheck]:
    out = []
    w, h = int(meta.get("width") or 0), int(meta.get("height") or 0)
    out.append(
        QACheck(
            "image_min_width",
            w >= policy.min_width,
            Severity.BLOCKER,
            1.0,
            f"{w}px < {policy.min_width}px",
            None if w >= policy.min_width else "Regenerate at higher resolution.",
        )
    )
    if policy.aspect and w and h:
        want = _ratio(policy.aspect)
        got = w / h
        ok = abs(got - want) / want < 0.02
        out.append(
            QACheck(
                "image_aspect",
                ok,
                Severity.BLOCKER,
                1.0,
                f"{got:.3f} vs {want:.3f}",
                None if ok else f"Output must be {policy.aspect}.",
            )
        )
    if product.attrs.color_hex and path:
        try:
            de = dominant_delta_e(path, product.attrs.color_hex, mask="center")
        except Exception:
            de = 0.0
        ok = de <= brand.palette_tolerance_de
        out.append(
            QACheck(
                "colour_fidelity",
                ok,
                Severity.MAJOR,
                max(0, 1 - de / 60),
                f"ΔE={de:.1f} vs {product.attrs.color_hex}",
                None
                if ok
                else f"The garment must read as {product.attrs.color} ({product.attrs.color_hex}).",
            )
        )
    if path:
        out.append(
            QACheck(
                "brand_palette",
                palette_overlap(path, brand.palette_hex) >= 0.25,
                Severity.MINOR,
                1.0,
                "scene palette off-brand",
                f"Bias the scene toward brand palette {brand.palette_hex[:3]}.",
            )
        )
        out.append(
            QACheck(
                "no_burnt_pixels",
                clipping_ratio(path) < 0.02,
                Severity.MINOR,
                1.0,
                "blown highlights",
                "Reduce exposure/contrast.",
            )
        )
    return out


def check_audio(meta, policy) -> list[QACheck]:
    lufs = float(meta.get("lufs", policy.loudness_lufs))
    peak = float(meta.get("true_peak", -1.0))
    rms = float(meta.get("rms_db", -20))
    lead = float(meta.get("lead_silence_s", 0))
    return [
        QACheck(
            "loudness",
            abs(lufs - policy.loudness_lufs) <= 1.5,
            Severity.MAJOR,
            1.0,
            f"{lufs:.1f} LUFS, target {policy.loudness_lufs}",
            "Re-normalise loudness.",
        ),
        QACheck("true_peak", peak <= -1.0, Severity.MAJOR, 1.0, f"{peak:.1f} dBTP", "Limit true peak to -1 dBTP."),
        QACheck("not_silent", rms > -50, Severity.BLOCKER, 1.0, "audio is silent", None),
        QACheck(
            "no_long_lead_silence",
            lead < 0.6,
            Severity.MINOR,
            1.0,
            f"{lead:.2f}s",
            "Trim leading silence.",
        ),
    ]


def check_video(meta, srt, policy) -> list[QACheck]:
    lo, hi = policy.duration_s or (0, 999)
    d = float(meta.get("duration_s") or 0)
    out = [
        QACheck(
            "video_duration",
            lo <= d <= hi,
            Severity.BLOCKER,
            1.0,
            f"{d:.1f}s outside [{lo},{hi}]",
            f"Target {lo}-{hi} seconds.",
        ),
        QACheck("has_audio_track", bool(meta.get("has_audio", True)), Severity.BLOCKER, 1.0, "no audio stream", None),
        QACheck(
            "first_frame_not_black",
            float(meta.get("first_frame_luma", 40)) > 12,
            Severity.MAJOR,
            1.0,
            "opens on black",
            "Trim the black lead-in; open on the product.",
        ),
        QACheck(
            "pixfmt_compatible",
            meta.get("pix_fmt", "yuv420p") == "yuv420p",
            Severity.BLOCKER,
            1.0,
            str(meta.get("pix_fmt")),
            None,
        ),
        QACheck("faststart", bool(meta.get("faststart", True)), Severity.MINOR, 1.0, "moov not at front", None),
    ]
    if policy.subtitles:
        out.append(
            QACheck(
                "subtitles_present",
                bool(srt),
                Severity.MAJOR,
                1.0,
                "no subtitles",
                "Generate subtitles — most feed views are muted.",
            )
        )
    return out
