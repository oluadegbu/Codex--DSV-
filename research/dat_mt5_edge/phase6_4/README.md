# Reproduce Phase 6.4

From the repository root, using existing Python and Git only:

```sh
python research/dat_mt5_edge/phase6_4/verify.py
```

The verifier reads public repository artifacts and committed sanitized cache
metadata only. It never opens Windows cache files, contacts a broker or starts
MT5. It checks all baseline Git blob identities at commit
`dd345e7c643c2d209bd0ee7caa10b223d6cb0957`, allowing additions only under
`research/dat_mt5_edge/phase6_4/`. This preserves all 91 earlier files, including
Phase 6.2/6.3 added by subsequent work after the earlier local checkout.

Metadata duplicate candidates are grouped by symbol, area, filename, bytes and
filesystem UTC modification time across servers. These are **not** quote-content
duplicates, coverage measurements or certification. The script prints JSON to
stdout; saving it as `VERIFICATION.json` is an offline report operation only.
No strategy suite is rerun for this documentation/metadata assessment.

Zero-action fields in the output record this phase's observed activity; they are
not an automated audit of every VPS process or proof that the host has no trading
capability. Preservation and metadata grouping are the mechanically checked parts.
