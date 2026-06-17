"""
Input validators for the events app  [A03 / ASVS V5].
"""

from django.core.validators import RegexValidator

# Whitelist for event titles: letters, numbers, spaces and a small set of
# punctuation. Anything else (e.g. angle brackets used for XSS payloads) is
# rejected at validation time.
title_validator = RegexValidator(
    regex=r"^[\w\s.,\-:'&()]{3,200}$",
    message="Title may contain letters, numbers, spaces and . , - : ' & ( ) only.",
)
