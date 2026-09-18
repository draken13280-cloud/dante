from fcf.core.config import settings


def main() -> None:
    print("mode", settings.mode)
    print("providers", settings.providers)
    print("allow_live_publish", settings.allow_live_publish)
    if settings.mode == "live":
        missing = []
        if settings.providers.image == "replicate_flux" and not settings.replicate_api_token:
            missing.append("REPLICATE_API_TOKEN")
        if missing:
            raise SystemExit("missing " + ",".join(missing))
    print("preflight ok")


if __name__ == "__main__":
    main()
