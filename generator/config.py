"""
Tessaly Health synthetic data generator: all tunable assumptions in one place.

Every number in this file is an invented placeholder chosen to look plausible
for a mid-sized nonprofit health system. None comes from a real organization.
ASSUMPTIONS.md explains each block in plain language.
"""

SEED = 20261108

# Simulation window (inclusive). Day 0 = WINDOW_START.
WINDOW_START = "2023-01-01"
WINDOW_END = "2025-12-31"

# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------
FACILITIES = [
    # facility_id, name, facility_type, facility_group
    ("FAC-H1", "Tessaly Flagship Hospital", "hospital_flagship", "Flagship Hospital"),
    ("FAC-H2", "Tessaly Community Hospital North", "hospital_community", "Community North"),
    ("FAC-H3", "Tessaly Community Hospital South", "hospital_community", "Community South"),
    ("FAC-HH", "Tessaly Home Health", "home_health", "Home Health"),
    ("FAC-SO", "Tessaly System Office", "system_office", "System Office"),
] + [
    (f"FAC-C{n:02d}", f"Tessaly Clinic {n:02d}", "clinic", "Clinics") for n in range(1, 21)
]

# Nursing units: unit_name, facility, kind, turnover_tier, specialty_cert, RN, LPN, NA slots
# kind: inpatient | clinic | home_health | admin
NURSING_UNITS = [
    ("Intensive Care", "FAC-H1", "inpatient", "medium", True, 90, 0, 10),
    ("Step-Down", "FAC-H1", "inpatient", "high", True, 70, 0, 16),
    ("Medical-Surgical 1", "FAC-H1", "inpatient", "high", False, 65, 6, 22),
    ("Medical-Surgical 2", "FAC-H1", "inpatient", "high", False, 65, 6, 22),
    ("Medical-Surgical 3", "FAC-H1", "inpatient", "medium", False, 60, 6, 20),
    ("Emergency Department", "FAC-H1", "inpatient", "high", True, 100, 0, 22),
    ("Perioperative Services", "FAC-H1", "inpatient", "low", True, 75, 0, 12),
    ("Women and Infants", "FAC-H1", "inpatient", "low", True, 70, 0, 10),
    ("Behavioral Health", "FAC-H1", "inpatient", "high", False, 40, 6, 22),
    ("Float Pool", "FAC-H1", "inpatient", "medium", False, 45, 0, 10),
    ("Medical-Surgical", "FAC-H2", "inpatient", "high", False, 60, 8, 20),
    ("Intensive Care", "FAC-H2", "inpatient", "medium", True, 35, 0, 6),
    ("Emergency Department", "FAC-H2", "inpatient", "high", True, 50, 0, 12),
    ("Perioperative Services", "FAC-H2", "inpatient", "low", True, 30, 0, 6),
    ("Medical-Surgical", "FAC-H3", "inpatient", "high", False, 60, 8, 20),
    ("Intensive Care", "FAC-H3", "inpatient", "medium", True, 35, 0, 6),
    ("Emergency Department", "FAC-H3", "inpatient", "high", True, 50, 0, 12),
    ("Perioperative Services", "FAC-H3", "inpatient", "low", True, 30, 0, 6),
    ("Home Health East", "FAC-HH", "home_health", "medium", False, 60, 15, 25),
    ("Home Health West", "FAC-HH", "home_health", "medium", False, 60, 15, 25),
    ("Nursing Administration", "FAC-SO", "admin", "low", False, 30, 0, 0),
] + [
    ("Clinic Nursing", f"FAC-C{n:02d}", "clinic", "low", False, 10, 6, 7) for n in range(1, 21)
]

# Non-nursing departments: dept_name, facility, role_code, headcount
DEPARTMENTS = []
for fac, scale in (("FAC-H1", 1.0), ("FAC-H2", 0.33), ("FAC-H3", 0.33)):
    for dept, role, base in (
        ("Imaging", "IMG", 75), ("Laboratory", "LAB", 85), ("Pharmacy", "PHA", 55),
        ("Rehabilitation Therapy", "THR", 60), ("Respiratory Therapy", "RSP", 55),
        ("Sterile Processing", "SPD", 40), ("Patient Access", "ADM", 65),
        ("Environmental Services", "EVS", 145), ("Facilities", "FAC", 60),
        ("Food and Nutrition", "FNS", 70),
    ):
        DEPARTMENTS.append((dept, fac, role, max(4, round(base * scale))))
DEPARTMENTS += [
    ("Rehabilitation Therapy", "FAC-HH", "THR", 40),
    ("Home Health Administration", "FAC-HH", "ADM", 30),
    ("Finance", "FAC-SO", "ADM", 80), ("Human Resources", "FAC-SO", "ADM", 60),
    ("Information Technology", "FAC-SO", "ADM", 120), ("Revenue Cycle", "FAC-SO", "ADM", 150),
    ("Quality and Safety", "FAC-SO", "ADM", 30), ("Clinical Education", "FAC-SO", "ADM", 20),
    ("Executive Administration", "FAC-SO", "ADM", 40),
]
for n in range(1, 21):
    DEPARTMENTS.append(("Clinic Support", f"FAC-C{n:02d}", "CSA", 6))
    DEPARTMENTS.append(("Clinic Front Desk", f"FAC-C{n:02d}", "ADM", 6))

ROLES = {
    # role_code: (role_name, role_family, licensed)
    "RN": ("Registered Nurse", "nursing", True),
    "LPN": ("Licensed Practical Nurse", "nursing", True),
    "NA": ("Nursing Assistant", "nursing", False),
    "NMGR": ("Nurse Manager", "nursing", True),
    "IMG": ("Imaging Technologist", "clinical_support", True),
    "LAB": ("Laboratory Technologist", "clinical_support", True),
    "PHA": ("Pharmacy Staff", "clinical_support", True),
    "THR": ("Therapist", "clinical_support", True),
    "RSP": ("Respiratory Therapist", "clinical_support", True),
    "SPD": ("Sterile Processing Technician", "clinical_support", False),
    "CSA": ("Clinical Support Associate", "clinical_support", False),
    "ADM": ("Administrative Staff", "administrative", False),
    "EVS": ("Environmental Services Associate", "facilities_evs", False),
    "FAC": ("Facilities Technician", "facilities_evs", False),
    "FNS": ("Food and Nutrition Associate", "facilities_evs", False),
    "DMGR": ("Department Manager", "administrative", False),
}

# FTE mix for staff (value: probability)
FTE_MIX = {1.0: 0.62, 0.9: 0.14, 0.75: 0.10, 0.6: 0.09, 0.5: 0.05}

# ---------------------------------------------------------------------------
# Turnover (annual probability of leaving, years 2+). Year 1 is multiplied.
# ---------------------------------------------------------------------------
VOLUNTARY_TURNOVER = {
    # (role group, tier or kind) -> annual probability
    ("rn", "high"): 0.17, ("rn", "medium"): 0.13, ("rn", "low"): 0.10,
    ("rn", "clinic"): 0.11, ("rn", "home_health"): 0.15, ("rn", "admin"): 0.08,
    ("lpn_na", "high"): 0.22, ("lpn_na", "medium"): 0.18, ("lpn_na", "low"): 0.15,
    ("lpn_na", "clinic"): 0.16, ("lpn_na", "home_health"): 0.20,
    ("clinical_support", None): 0.14, ("administrative", None): 0.12,
    ("facilities_evs", None): 0.22, ("manager", None): 0.07,
}
INVOLUNTARY_TURNOVER = 0.02
FIRST_YEAR_HAZARD_MULTIPLIER = 2.0

# Initial tenure (years) for staff in place on day 0: gamma(shape, scale), capped
INITIAL_TENURE_GAMMA = (1.3, 5.0)
INITIAL_TENURE_CAP_YEARS = 35
# Share of slots vacant on day 0, by tier (non-nursing uses "other")
INITIAL_VACANCY = {"high": 0.08, "medium": 0.05, "low": 0.03, "other": 0.04}
# Budgeted RN positions that stay open the whole window (hard to fill), by tier
CHRONIC_RN_VACANCY = {"high": 0.06, "medium": 0.04, "low": 0.02}

# Days to fill a vacancy: gamma with this mean (shape 2)
FILL_DAYS_MEAN = {"rn_high": 95, "rn_other": 75, "other": 45}
INTERNAL_TRANSFER_SHARE = {"RN": 0.10, "other": 0.06}
REHIRE_SHARE = 0.05            # of external fills, drawn from prior voluntary leavers
REHIRE_MIN_GAP_DAYS = 60
NEW_GRAD_SHARE_RN = {"inpatient": 0.35, "other": 0.05}

# ---------------------------------------------------------------------------
# Planted causal effects (the "truth" the case studies try to recover)
# ---------------------------------------------------------------------------
# Applied as hazard ratios on year-1 voluntary turnover only.
HR_ONBOARDING_ON_TIME = 0.70       # role onboarding finished within 30 days (sized to be detectable at ~2,300 hires)
HR_RESIDENCY_HIGH_ATTENDER = 0.65  # new-grad RN with attendance propensity >= 0.80
RESIDENCY_HIGH_ATTENDER_CUTOFF = 0.80

# Onboarding on-time probability (confounded: lower on high-turnover units)
ONBOARDING_ON_TIME_BASE = 0.80
ONBOARDING_ON_TIME_HIGH_TIER_PENALTY = 0.15
ONBOARDING_NEVER_SHARE = 0.05

# Residency attendance propensity per new-grad RN: Beta(a, b), minus penalty on high tier
RESIDENCY_ATTENDANCE_BETA = (5, 2)
RESIDENCY_HIGH_TIER_PENALTY = 0.10
RESIDENCY_COHORT_MONTHS = (2, 6, 9)
RESIDENCY_SESSIONS = 12
RESIDENCY_COMPLETION_MIN_SESSIONS = 10

# Time to proficiency (days): gamma with mean and sd
PROFICIENCY_DAYS = {
    "new_grad_high_attender": (140, 35),
    "new_grad_low_attender": (170, 45),
    "experienced_hire": (75, 25),
    "agency": (12, 4),
}
PROFICIENCY_SPECIALTY_MULTIPLIER = 1.2   # ICU, ED, Step-Down
ORIENTATION_DAYS_NOT_COUNTED_IN_STAFFING = 14

# ---------------------------------------------------------------------------
# Staffing (case study C)
# ---------------------------------------------------------------------------
RN_WEEKLY_HOURS_AT_1FTE = 36
ABSENCE_RATE_MEAN = 0.07
ABSENCE_RATE_SD = 0.02
DEMAND_NOISE_SD = 0.04
WINTER_DEMAND_UPLIFT = 0.06      # Dec-Feb
SUMMER_DEMAND_DIP = -0.03        # Jul-Aug
# Budgeted RN positions fall short of typical demand by this share (by tier)
STRUCTURAL_SHORTFALL = {"high": 0.0, "medium": 0.0, "low": 0.0}
OVERTIME_SHARE_OF_GAP = (0.25, 0.40)
OVERTIME_SHARE_OF_GAP_NO_AGENCY = (0.60, 0.80)
OVERTIME_CAP_SHARE_OF_REQUIRED = 0.12
AGENCY_CONTRACT_WEEKS = 13
AGENCY_EXTENSION_PROB = 0.25
AGENCY_LEAD_DAYS = 14
AGENCY_BOOKING_FACTOR = 0.9      # book contracts to cover 90% of recent residual gap
AGENCY_UNIT_TIERS = ("high", "medium")
AGENCIES = ("Agency A", "Agency B", "Agency C")

# Cost assumptions (USD). National public benchmarks; see ASSUMPTIONS.md for sources.
# Tessaly is fictional, so these are national averages, not a real local market.
COSTS = {
    # wage per hour worked, RN in private hospitals (BLS ECEC Dec 2024 = 51.09);
    # 2023 and 2025 scaled by roughly 4% a year (BLS OEWS median growth), approximate
    "staff_rn_wage_per_hour_worked": {2023: 49.10, 2024: 51.09, 2025: 53.24},
    "benefits_load_on_wages_pct": 0.56,    # BLS ECEC Dec 2024: 28.43 / 51.09
    "overtime_multiplier": 1.5,             # FLSA minimum premium
    "agency_rn_bill_rate": {2023: 106.63, 2024: 90.13, 2025: 90.54},  # SIA/NATHO survey
    "cost_per_rn_turnover": {2024: 61110, 2025: 60090},               # NSI 2025, 2026 reports
    "agency_orientation_cost_per_contract": 1200,                     # invented
}

# ---------------------------------------------------------------------------
# Learning (case studies A, B, D)
# ---------------------------------------------------------------------------
CAMPAIGN_ASSIGN = "02-01"
CAMPAIGN_DUE = "04-30"
NEW_HIRE_COMPLIANCE_FROM = "01-15"   # hires on/after this date get current-year modules at hire
NEW_HIRE_COMPLIANCE_DUE_DAYS = 30

CAMPAIGN_ON_TIME_BASE = 0.88
CAMPAIGN_LATE_SHARE_OF_REST = 0.65
CAMPAIGN_SKIP_ONE_MODULE = 0.04
PERSON_PROPENSITY_SD = 0.6
UNIT_PROPENSITY_SD = 0.3
HIGH_TIER_PROPENSITY_SHIFT = -0.3
ASSESSMENT_FAIL_RATE = 0.07
RETAKE_FAIL_RATE = 0.10
LEAVE_EXEMPTION_RATE = 0.025
EQUIVALENT_CREDIT_RATE = 0.01
CANCEL_ON_TERMINATION_SHARE = 0.30

CERT_RENEWAL_LEAD_DAYS = 60
CERT_ON_TIME = 0.85
CERT_LATE = 0.10

SELF_ENROLL_RATE = 0.06
PRECEPTOR_ASSIGN_RATE = 0.08

# LMS account behavior
FEED_DEACTIVATION_LONG_LAG_SHARE = 0.05
REHIRE_NEW_ACCOUNT_SHARE = 0.30
MANUAL_DUPLICATE_ACCOUNT_SHARE = 0.02
AGENCY_EXTERNAL_ID_POPULATED = 0.75
TEST_ACCOUNTS = 6

# Data-quality defects sprinkled at random (rates)
DQ_DUPLICATE_ATTEMPT_ROWS = 0.004
DQ_COMPLETED_WITHOUT_ATTEMPT = 0.002
DQ_DUE_BEFORE_ASSIGNED = 0.003
DQ_OLD_VERSION_COMPLETION = 0.02     # of 2025 Information Security completers

HR_FEED_RANDOM_FAILURES = 4          # in addition to the planted outage
HR_FEED_PLANTED_OUTAGE = ("2024-08-27", "2024-08-29")
