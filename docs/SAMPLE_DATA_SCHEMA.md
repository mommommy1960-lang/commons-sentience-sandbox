# Sample Data Schema

> **File:** `data/sample_fermi_lat_grb_events.csv`  
> **Purpose:** Local representative sample for adapter testing and dry-run validation.  
> **Status:** Synthetic-but-realistic — values inspired by published Fermi-LAT GRB catalogs.  
> **Do NOT treat as real scientific data.**

---

## 1. Column Definitions

| Column | Type | Unit | Required | Description |
|---|---|---|---|---|
| `event_id` | string | — | ✅ | Unique photon event identifier (e.g. `EVT_001`) |
| `source_id` | string | — | ✅ | GRB name, e.g. `GRB080916C` (year/month/day + letter) |
| `photon_energy` | float | GeV | ✅ | Reconstructed photon energy in the LAT energy band |
| `arrival_time` | float | seconds | ✅ | Time since the first photon in this burst (trigger-relative) |
| `redshift` | float | — | optional | Spectroscopic redshift `z` of the host galaxy; used to derive luminosity distance |

---

## 2. Adapter Column Mapping

The `fermi_lat_grb_adapter` maps these columns via its synonym detection table:

| CSV column | Canonical adapter key | Notes |
|---|---|---|
| `event_id` | `event_id` | direct match |
| `source_id` | `source_id` | direct match; synonyms: `source`, `grb_name`, `burst` |
| `photon_energy` | `photon_energy` | direct match; synonyms: `energy`, `e_gev`, `energy_gev` |
| `arrival_time` | `arrival_time` | direct match; synonyms: `time`, `time_s`, `t_s`, `t` |
| `redshift` | `redshift` | direct match; synonyms: `z`, `z_spec` |

---

## 3. Physical Coverage

The 5 GRBs in the sample span a range typical of Fermi-LAT High-Energy (HE) GRB catalog entries:

| GRB | Redshift z | Luminosity distance (approx.) | Energy range (GeV) | Notes |
|---|---|---|---|---|
| GRB080916C | 4.35 | ~40 Gpc | 0.10 – 13.2 | Fermi-LAT first year flagship |
| GRB090902B | 1.822 | ~14 Gpc | 0.09 – 10.1 | High-energy photon at 33.4 GeV in real data |
| GRB090510  | 0.903 | ~6 Gpc | 0.16 – 30.5 | Short GRB; highest-energy photon 30.5 GeV |
| GRB130427A | 0.340 | ~2 Gpc | 0.07 – 94.0 | Brightest GRB observed; 95 GeV photon in real |
| GRB160509A | 1.170 | ~8 Gpc | 0.11 – 11.7 | Long GRB; moderate energy range |

> Energy and timing values are illustrative, not extracted from real FITS data.

---

## 4. Adapter Output Schema

After running through `load_grb_events()`, each event in `output["events"]` has:

```json
{
  "event_id": "EVT_001",
  "energy": 0.1035,
  "time": 0.0,
  "source": "GRB080916C",
  "redshift": 4.35,
  "distance_Mpc": <flat ΛCDM estimate>
}
```

`time` is normalized to seconds since the earliest photon **within each source group**.

`distance_Mpc` is computed via flat ΛCDM approximation:
$$D_L \approx \frac{c}{H_0} \cdot z \cdot \left(1 + \frac{z}{2}\right)$$
with $H_0 = 67.4$ km/s/Mpc, $c = 2.998 \times 10^5$ km/s.

---

## 5. Intended Uses

| Use case | Correct? | Notes |
|---|---|---|
| Adapter unit tests | ✅ | Primary purpose |
| Pipeline dry-run (freeze_immediately=True) | ✅ | Safe; null result expected |
| Null-model validation | ✅ | Data generated with no injected LIV signal |
| Science claim derivation | ❌ | Synthetic data; not real Fermi-LAT FITS |
| Hardware trigger | ❌ | Not physical data |

---

## 6. Real Public-Data Equivalent

When real Fermi-LAT GRB data is ready to ingest, it will come from:

- **Fermi-LAT Performance Data**: https://www.slac.stanford.edu/exp/glast/groups/canda/lat_Performance.htm
- **Fermi-LAT LAT EventFile**: event-level FITS files from the Fermi Science Support Center (FSSC)
- **2FLGC / 1FLGC**: Fermi LAT GRB Catalog (event tables in FITS or released ASCII)

The columns used in the real files may differ; use `column_map` override in `load_grb_events()` to remap.

---

*Schema version: 1.0 — maintained in `reality_audit/adapters/fermi_lat_grb_adapter.py`*
