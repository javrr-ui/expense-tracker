# Code Smell: Dead Code (PAYPAL Bank Definition)

**Labels:** `code-quality`, `cleanup`, `low-priority`  
**Type:** Dead Code

## Description

`SupportedBanks.PAYPAL` is defined in the enum and has email addresses configured in `bank_emails`, but the `PayPalParser` is commented out in the parsers dictionary. This creates confusion about whether PayPal is actually supported.

## Locations

- `constants/banks.py` (line 22) - PAYPAL enum value defined
- `constants/banks.py` (line 38) - PAYPAL email addresses configured
- `core/parsers/parser_helper.py` (line 24) - PayPalParser commented out

## Current Code

```python
# In constants/banks.py
class SupportedBanks(StrEnum):
    HEY_BANCO = "hey_banco"
    NUBANK = "nubank"
    RAPPI = "rappi"
    PAYPAL = "paypal"  # ← Defined but not used
    BANORTE = "banorte"

bank_emails = {
    # ... other banks
    SupportedBanks.PAYPAL: ["service@paypal.com.mx"],  # ← Configured but not used
    # ...
}

# In core/parsers/parser_helper.py
PARSERS = {
    SupportedBanks.HEY_BANCO: HeyBancoParser(),
    SupportedBanks.NUBANK: NubankParser(),
    SupportedBanks.RAPPI: RappiParser(),
    # SupportedBanks.PAYPAL: PayPalParser(),  # ← Commented out
    SupportedBanks.BANORTE: BanorteParser(),
}
```

## Impact

- **Confusion:** Unclear whether PayPal is supported or not
- **Code Bloat:** Unused constants taking up space
- **Potential Bugs:** If someone enables PAYPAL thinking it's ready
- **Documentation:** README doesn't mention PayPal as unsupported

## Options for Resolution

### Option 1: Remove if not ready
If PayPal support is not implemented yet, remove it entirely:

```python
# Remove from constants/banks.py
class SupportedBanks(StrEnum):
    HEY_BANCO = "hey_banco"
    NUBANK = "nubank"
    RAPPI = "rappi"
    # PAYPAL can be added when ready
    BANORTE = "banorte"

# Remove from bank_emails
bank_emails = {
    # ... (no PAYPAL entry)
}
```

### Option 2: Implement if intended
If PayPal support is intended, implement the parser:

```python
# Create core/parsers/paypal.py
class PayPalParser(BaseBankParser):
    bank_name = SupportedBanks.PAYPAL
    
    def parse(self, email_message, email_id: str) -> Transaction | None:
        # Implementation
        pass

# Uncomment in parser_helper.py
PARSERS = {
    # ...
    SupportedBanks.PAYPAL: PayPalParser(),
}
```

### Option 3: Mark as planned
If PayPal support is planned but not ready, add a comment:

```python
# In constants/banks.py
class SupportedBanks(StrEnum):
    HEY_BANCO = "hey_banco"
    NUBANK = "nubank"
    RAPPI = "rappi"
    PAYPAL = "paypal"  # TODO: Implement PayPalParser (planned)
    BANORTE = "banorte"

# In parser_helper.py
PARSERS = {
    SupportedBanks.HEY_BANCO: HeyBancoParser(),
    SupportedBanks.NUBANK: NubankParser(),
    SupportedBanks.RAPPI: RappiParser(),
    # TODO: Implement PayPalParser
    # SupportedBanks.PAYPAL: PayPalParser(),
    SupportedBanks.BANORTE: BanorteParser(),
}
```

## Recommended Approach

**Option 1** (Remove) is recommended unless PayPal implementation is actively being worked on. It reduces confusion and keeps the codebase clean.

## Acceptance Criteria

- [ ] Decide on approach (remove, implement, or document as planned)
- [ ] Update `constants/banks.py` accordingly
- [ ] Update `parser_helper.py` accordingly
- [ ] Update README.md if needed to reflect PayPal status
- [ ] Remove or add PayPal from "próximos bancos" section in README

## Additional Notes

The README mentions PayPal in the "Soporte futuro para más bancos" section as a planned bank, so Option 3 (mark as planned) might be most appropriate.
