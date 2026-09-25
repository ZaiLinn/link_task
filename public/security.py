SENSITIVE_CONFIG_KEYS = {
    "token",
    "password",
    "secret",
    "api_hash",
    "bot_token",
    "okpay_token",
}


def mask_secret(value):
    if not value:
        return value
    value = str(value)
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}***{value[-4:]}"


def redact_config(config):
    redacted = {}
    for key, value in dict(config).items():
        key_lower = str(key).lower()
        if any(secret_key in key_lower for secret_key in SENSITIVE_CONFIG_KEYS):
            redacted[key] = mask_secret(value)
        else:
            redacted[key] = value
    return redacted
