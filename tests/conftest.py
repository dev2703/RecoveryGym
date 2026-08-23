import os

# Tests run without external API keys or GPU models.
os.environ.setdefault("USE_MOCK_WAM", "true")
os.environ.setdefault("SMOLVLA_ALLOW_FALLBACK", "true")
os.environ.setdefault("USE_MODAL_JOBS", "false")
os.environ.setdefault("RECOVERYGYM_ARTIFACTS_DIR", "./artifacts")
