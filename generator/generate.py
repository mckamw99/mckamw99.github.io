"""
Tessaly Health synthetic data generator (LIB-23).

AI-assisted (Claude). Validation checks are in validate.py.
All data is synthetic. Tessaly Health is a fictional organization.

Usage:  python generate.py [--out data]
Same seed, same output. Change parameters in config.py, not here.
"""
import argparse
import heapq
import json
import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import config as C

rng = np.random.default_rng(C.SEED)
D0 = date.fromisoformat(C.WINDOW_START)
END = (date.fromisoformat(C.WINDOW_END) - D0).days  # last simulated day index
YEARS = list(range(D0.year, date.fromisoformat(C.WINDOW_END).year + 1))


def d(day):
    """Day index -> ISO date string (None stays None)."""
    if day is None or (isinstance(day, float) and math.isnan(day)):
        return None
    return (D0 + timedelta(days=int(day))).isoformat()


def di(iso):
    return (date.fromisoformat(iso) - D0).days


def ymd(y, mmdd):
    return di(f"{y}-{mmdd}")


def gamma_mean_sd(mean, sd, size=None):
    shape = (mean / sd) ** 2
    return rng.gamma(shape, sd ** 2 / mean, size)


FIRST = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David",
         "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas",
         "Sarah", "Christopher", "Karen", "Daniel", "Lisa", "Matthew", "Nancy", "Anthony", "Betty",
         "Mark", "Sandra", "Steven", "Ashley", "Andrew", "Emily", "Joshua", "Michelle", "Kevin",
         "Amanda", "Brian", "Melissa", "Maria", "Deborah", "Luis", "Stephanie", "Jose", "Rebecca",
         "Aisha", "Laura", "Wei", "Amy", "Priya", "Angela", "Omar", "Nicole", "Carlos", "Rachel",
         "Darnell", "Megan", "Tyler", "Hannah", "Kenji", "Grace"]
LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
        "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor",
        "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez",
        "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright",
        "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall",
        "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Patel", "Kim", "Chen", "Okafor",
        "Murphy", "Kowalski", "Brooks", "Reyes", "Price", "Bennett"]

# ---------------------------------------------------------------------------
# 1. Reference tables
# ---------------------------------------------------------------------------
facilities = pd.DataFrame(C.FACILITIES, columns=["facility_id", "facility_name", "facility_type",
                                                  "facility_group"])
fac_group = dict(zip(facilities.facility_id, facilities.facility_group))

units, slots = [], []
uid = 0
for name, fac, kind, tier, spec, rn, lpn, na in C.NURSING_UNITS:
    uid += 1
    u = f"U{uid:03d}"
    units.append(dict(unit_id=u, unit_name=name, facility_id=fac, unit_kind=kind,
                      department_type="nursing", turnover_tier=tier, specialty_cert_required=spec,
                      budgeted_rn=rn, budgeted_lpn=lpn, budgeted_na=na))
    slots.append((u, "NMGR"))
    slots += [(u, "RN")] * rn + [(u, "LPN")] * lpn + [(u, "NA")] * na
for name, fac, role, n in C.DEPARTMENTS:
    uid += 1
    u = f"U{uid:03d}"
    units.append(dict(unit_id=u, unit_name=name, facility_id=fac, unit_kind="department",
                      department_type="non_nursing", turnover_tier=None,
                      specialty_cert_required=False, budgeted_rn=0, budgeted_lpn=0, budgeted_na=0))
    slots.append((u, "DMGR"))
    slots += [(u, role)] * n
U = {u["unit_id"]: {k: v for k, v in u.items() if k != "unit_id"} for u in units}
units = pd.DataFrame(units)
slots = pd.DataFrame(slots, columns=["unit_id", "role_code"])
slots.insert(0, "slot_id", [f"S{i:05d}" for i in range(1, len(slots) + 1)])
SLOT = slots.set_index("slot_id").to_dict("index")
roles = pd.DataFrame([(k, *v) for k, v in C.ROLES.items()],
                     columns=["role_code", "role_name", "role_family", "licensed"])
ROLE_FAMILY = {k: v[1] for k, v in C.ROLES.items()}


def tier_key(unit_id):
    u = U[unit_id]
    if u["unit_kind"] == "inpatient":
        return u["turnover_tier"]
    return {"clinic": "clinic", "home_health": "home_health", "admin": "admin"}.get(u["unit_kind"])


def annual_vol_rate(role, unit_id):
    if role in ("NMGR", "DMGR"):
        return C.VOLUNTARY_TURNOVER[("manager", None)]
    if role == "RN":
        return C.VOLUNTARY_TURNOVER[("rn", tier_key(unit_id))]
    if role in ("LPN", "NA"):
        return C.VOLUNTARY_TURNOVER[("lpn_na", tier_key(unit_id))]
    return C.VOLUNTARY_TURNOVER[(ROLE_FAMILY[role], None)]


def to_rate(p_annual):
    return -math.log(1 - p_annual) / 365.0


def draw_exit(start_day, tenure_at_start, role, unit_id, hr_year1=1.0):
    """Piecewise-exponential time to exit. Returns (exit_day, type) or (None, None)."""
    vol = to_rate(annual_vol_rate(role, unit_id))
    inv = to_rate(C.INVOLUNTARY_TURNOVER)
    t = start_day
    ten = tenure_at_start
    if ten < 365:
        r1v = vol * C.FIRST_YEAR_HAZARD_MULTIPLIER * hr_year1
        total = r1v + inv
        dt = rng.exponential(1 / total)
        if dt < 365 - ten:
            return int(t + dt), ("voluntary" if rng.random() < r1v / total else "involuntary")
        t += 365 - ten
    total = vol + inv
    dt = rng.exponential(1 / total)
    return int(t + dt), ("voluntary" if rng.random() < vol / total else "involuntary")


def fill_lag(role, unit_id):
    if role == "RN":
        m = C.FILL_DAYS_MEAN["rn_high" if U[unit_id]["turnover_tier"] == "high" else "rn_other"]
    else:
        m = C.FILL_DAYS_MEAN["other"]
    return int(max(5, rng.gamma(2, m / 2)))


FTE_VALUES = np.array(list(C.FTE_MIX.keys()))
FTE_P = np.array(list(C.FTE_MIX.values()))

# ---------------------------------------------------------------------------
# 2. Workforce simulation (event-driven)
# ---------------------------------------------------------------------------
persons = {}         # person_id -> dict
workers = {}         # employee_id -> dict
history = []         # unit history rows
slot_occ = {}        # slot_id -> employee_id or None
active_by_role = {}  # role -> set of employee_ids
former_vol = {}      # role -> list of (employee_id, term_day)
events = []
seq = 0
pid_counter = 0
eid_counter = 0


def push(day, kind, payload):
    global seq
    seq += 1
    heapq.heappush(events, (day, seq, kind, payload))


def new_person():
    global pid_counter
    pid_counter += 1
    pid = f"P{pid_counter:06d}"
    persons[pid] = dict(person_id=pid, first_name=str(rng.choice(FIRST)),
                        last_name=str(rng.choice(LAST)))
    return pid


def onboarding_and_residency(role, unit_id, new_grad):
    """Draw training exposures that also shift year-1 hazard (the planted effects)."""
    high = U[unit_id]["turnover_tier"] == "high"
    hr = 1.0
    p_on = C.ONBOARDING_ON_TIME_BASE - (C.ONBOARDING_ON_TIME_HIGH_TIER_PENALTY if high else 0)
    r = rng.random()
    if r < C.ONBOARDING_NEVER_SHARE:
        ob_day, on_time = None, False
    elif r < C.ONBOARDING_NEVER_SHARE + (1 - C.ONBOARDING_NEVER_SHARE) * p_on:
        ob_day, on_time = int(rng.integers(3, 31)), True
    else:
        ob_day, on_time = int(31 + rng.exponential(25)), False
    if on_time:
        hr *= C.HR_ONBOARDING_ON_TIME
    att = None
    if new_grad:
        att = float(rng.beta(*C.RESIDENCY_ATTENDANCE_BETA)) - (C.RESIDENCY_HIGH_TIER_PENALTY if high else 0)
        att = min(max(att, 0.05), 0.99)
        if att >= C.RESIDENCY_HIGH_ATTENDER_CUTOFF:
            hr *= C.HR_RESIDENCY_HIGH_ATTENDER
    return ob_day, on_time, att, hr


def hire(slot_id, day, person_id=None, rehire_of=None, initial_tenure=None):
    global eid_counter
    s = SLOT[slot_id]
    role, unit_id = s["role_code"], s["unit_id"]
    eid_counter += 1
    eid = f"E{eid_counter:06d}"
    pid = person_id or new_person()
    initial = initial_tenure is not None
    hire_day = day - initial_tenure if initial else day
    new_grad = False
    if role == "RN" and not initial and rehire_of is None:
        share = C.NEW_GRAD_SHARE_RN["inpatient" if U[unit_id]["unit_kind"] == "inpatient" else "other"]
        new_grad = bool(rng.random() < share)
    if initial:
        ob_day, on_time, att, hr = None, None, None, 1.0
    else:
        ob_day, on_time, att, hr = onboarding_and_residency(role, unit_id, new_grad)
    w = dict(employee_id=eid, person_id=pid, role_code=role, hire_unit_id=unit_id,
             current_unit_id=unit_id, slot_id=slot_id, fte=float(rng.choice(FTE_VALUES, p=FTE_P)),
             hire_day=hire_day, term_day=None, term_type=None, rehire=rehire_of is not None,
             prior_employee_id=rehire_of, new_grad=new_grad, in_window_hire=not initial,
             onboarding_days=ob_day, onboarding_on_time=on_time, residency_propensity=att,
             last_transfer_day=-9999)
    workers[eid] = w
    slot_occ[slot_id] = eid
    active_by_role.setdefault(role, set()).add(eid)
    history.append(dict(employee_id=eid, unit_id=unit_id, start_day=hire_day, end_day=None,
                        change_reason="rehire" if rehire_of else "hire"))
    ten = initial_tenure if initial else 0
    xday, xtype = draw_exit(day, ten, role, unit_id, hr)
    push(xday, "exit", (eid, xtype))
    return eid


def close_history(eid, day):
    for h in reversed(history):
        if h["employee_id"] == eid and h["end_day"] is None:
            h["end_day"] = day
            return


# Initial population
for slot_id, s in SLOT.items():
    tier = U[s["unit_id"]]["turnover_tier"] or "other"
    if s["role_code"] == "RN" and tier in C.CHRONIC_RN_VACANCY and rng.random() < C.CHRONIC_RN_VACANCY[tier]:
        slot_occ[slot_id] = None  # never filled
        continue
    if rng.random() < C.INITIAL_VACANCY[tier]:
        slot_occ[slot_id] = None
        push(int(rng.integers(0, 60)), "fill", slot_id)
    else:
        ten_years = min(rng.gamma(*C.INITIAL_TENURE_GAMMA), C.INITIAL_TENURE_CAP_YEARS)
        hire(slot_id, 0, initial_tenure=max(1, int(ten_years * 365)))

while events:
    day, _, kind, payload = heapq.heappop(events)
    if day > END:
        break
    if kind == "exit":
        eid, xtype = payload
        w = workers[eid]
        if w["term_day"] is not None:
            continue
        w["term_day"], w["term_type"] = day, xtype
        close_history(eid, day)
        active_by_role[w["role_code"]].discard(eid)
        slot_occ[w["slot_id"]] = None
        push(day + fill_lag(w["role_code"], w["current_unit_id"]), "fill", w["slot_id"])
        if xtype == "voluntary":
            former_vol.setdefault(w["role_code"], []).append((eid, day))
    elif kind == "fill":
        slot_id = payload
        if slot_occ.get(slot_id):
            continue
        s = SLOT[slot_id]
        role, unit_id = s["role_code"], s["unit_id"]
        share = C.INTERNAL_TRANSFER_SHARE["RN" if role == "RN" else "other"]
        moved = False
        if role not in ("NMGR", "DMGR") and rng.random() < share:
            kind_here = U[unit_id]["unit_kind"]
            cands = [e for e in sorted(active_by_role.get(role, ()))
                     if workers[e]["current_unit_id"] != unit_id
                     and U[workers[e]["current_unit_id"]]["unit_kind"] == kind_here
                     and day - workers[e]["hire_day"] > 180
                     and day - workers[e]["last_transfer_day"] > 365]
            if cands:
                eid = cands[int(rng.integers(len(cands)))]
                w = workers[eid]
                old_slot = w["slot_id"]
                close_history(eid, day - 1)
                history.append(dict(employee_id=eid, unit_id=unit_id, start_day=day, end_day=None,
                                    change_reason="transfer"))
                w.update(current_unit_id=unit_id, slot_id=slot_id, last_transfer_day=day)
                slot_occ[slot_id] = eid
                slot_occ[old_slot] = None
                push(day + fill_lag(role, SLOT[old_slot]["unit_id"]), "fill", old_slot)
                moved = True
        if moved:
            continue
        pool = [x for x in former_vol.get(role, []) if day - x[1] >= C.REHIRE_MIN_GAP_DAYS
                and not workers[x[0]].get("rehired")]
        if pool and rng.random() < C.REHIRE_SHARE:
            prev_eid, _ = pool[int(rng.integers(len(pool)))]
            workers[prev_eid]["rehired"] = True
            hire(slot_id, day, person_id=workers[prev_eid]["person_id"], rehire_of=prev_eid)
        else:
            hire(slot_id, day)

hist = pd.DataFrame(history)

# ---------------------------------------------------------------------------
# 3. Residency, proficiency
# ---------------------------------------------------------------------------
def first_cohort_after(day):
    for y in YEARS + [YEARS[-1] + 1]:
        for m in C.RESIDENCY_COHORT_MONTHS:
            cd = (date(y, m, 10) - D0).days
            if cd >= day + 14:
                return y, m, cd
    return None


def add_months(y, m, k):
    m2 = m - 1 + k
    return y + m2 // 12, m2 % 12 + 1


residents, attendance = [], []
for eid, w in workers.items():
    if not w["new_grad"]:
        continue
    y, m, cd = first_cohort_after(w["hire_day"])
    cohort = f"NR-{y}-{m:02d}"
    attended = 0
    last_session_day = None
    for k in range(C.RESIDENCY_SESSIONS):
        yy, mm = add_months(y, m, k)
        sday = (date(yy, mm, 10) - D0).days
        if sday > END:
            break
        if w["term_day"] is not None and w["term_day"] < sday:
            break
        a = rng.random() < w["residency_propensity"]
        attended += a
        last_session_day = sday
        attendance.append(dict(employee_id=eid, cohort_id=cohort, session_no=k + 1,
                               session_date=d(sday), attended=bool(a)))
    final_held = last_session_day is not None and (
        (date(*add_months(y, m, C.RESIDENCY_SESSIONS - 1), 10) - D0).days == last_session_day)
    completed = final_held and attended >= C.RESIDENCY_COMPLETION_MIN_SESSIONS
    w["residency_cohort"] = cohort
    w["residency_complete_day"] = last_session_day if completed else None
    residents.append(dict(employee_id=eid, cohort_id=cohort, cohort_start_date=d(cd),
                          sessions_attended=attended, residency_completed=bool(completed),
                          completion_date=d(last_session_day) if completed else None))

SPECIALTY_NAMES = ("Intensive Care", "Emergency Department", "Step-Down")
proficiency = []
for eid, w in workers.items():
    if w["role_code"] != "RN" or not w["in_window_hire"]:
        continue
    u = U[w["hire_unit_id"]]
    if u["unit_kind"] != "inpatient":
        continue
    if w["new_grad"]:
        path = ("new_grad_high_attender" if w["residency_propensity"] >= C.RESIDENCY_HIGH_ATTENDER_CUTOFF
                else "new_grad_low_attender")
    else:
        path = "experienced_hire"
    mean, sd = C.PROFICIENCY_DAYS[path]
    days = float(gamma_mean_sd(mean, sd))
    if u["unit_name"] in SPECIALTY_NAMES:
        days *= C.PROFICIENCY_SPECIALTY_MULTIPLIER
    days = int(round(days))
    pday = w["hire_day"] + days
    reached = pday <= END and (w["term_day"] is None or pday < w["term_day"])
    proficiency.append(dict(subject_type="staff", subject_id=eid, unit_id=w["hire_unit_id"],
                            pathway="new_grad" if w["new_grad"] else "experienced_hire",
                            start_date=d(w["hire_day"]), proficient_date=d(pday) if reached else None,
                            days_to_proficiency=days if reached else None,
                            censored=not reached))

# ---------------------------------------------------------------------------
# 4. Staffing by unit-day and agency contracts (case study C)
# ---------------------------------------------------------------------------
ndays = END + 1
inpatient = units[units.unit_kind == "inpatient"].unit_id.tolist()
rn_fte = {u: np.zeros(ndays + 2) for u in inpatient}
for h in history:
    w = workers[h["employee_id"]]
    if w["role_code"] != "RN" or h["unit_id"] not in rn_fte:
        continue
    start = h["start_day"]
    if h["change_reason"] in ("hire", "rehire") and w["in_window_hire"]:
        start += C.ORIENTATION_DAYS_NOT_COUNTED_IN_STAFFING
    end = h["end_day"] if h["end_day"] is not None else END
    s, e = max(start, 0), min(end, END)
    if s > e:
        continue
    rn_fte[h["unit_id"]][s] += w["fte"]
    rn_fte[h["unit_id"]][e + 1] -= w["fte"]
daily_hours_per_fte = C.RN_WEEKLY_HOURS_AT_1FTE / 7
dates = [D0 + timedelta(days=i) for i in range(ndays)]
season = np.array([C.WINTER_DEMAND_UPLIFT if dt.month in (12, 1, 2) else
                   C.SUMMER_DEMAND_DIP if dt.month in (7, 8) else 0.0 for dt in dates])

staffing_rows, contracts, agency_workers = [], [], []
ctr = 0
aw_ctr = 0
mean_fte = float((FTE_VALUES * FTE_P).sum())
for u in inpatient:
    fte_series = np.cumsum(rn_fte[u])[:ndays]
    base = U[u]["budgeted_rn"] * mean_fte * daily_hours_per_fte * (1 - C.ABSENCE_RATE_MEAN) \
        * (1 + C.STRUCTURAL_SHORTFALL[U[u]["turnover_tier"]])
    required = base * (1 + season + rng.normal(0, C.DEMAND_NOISE_SD, ndays))
    absence = np.clip(rng.normal(C.ABSENCE_RATE_MEAN, C.ABSENCE_RATE_SD, ndays), 0, 0.2)
    available = fte_series * daily_hours_per_fte * (1 - absence)
    agency_cap = np.zeros(ndays + 600)
    residual_hist = np.zeros(ndays)
    books_agency = U[u]["turnover_tier"] in C.AGENCY_UNIT_TIERS
    active_contracts = []  # (start, end, agency_worker_id)
    for t in range(ndays):
        if books_agency and dates[t].day == 1 and t >= 1:
            window = residual_hist[max(0, t - 28):t]
            need = window.mean() if len(window) else 0
            active_at_lead = sum(1 for s, e, _ in active_contracts if s <= t + C.AGENCY_LEAD_DAYS <= e)
            target = int(round(need * C.AGENCY_BOOKING_FACTOR / daily_hours_per_fte))
            for _ in range(max(0, target - active_at_lead)):
                ctr += 1
                aw_ctr += 1
                awid = f"AW{aw_ctr:05d}"
                agency_workers.append(dict(agency_worker_id=awid, agency_name=str(rng.choice(C.AGENCIES)),
                                           first_name=str(rng.choice(FIRST)), last_name=str(rng.choice(LAST)),
                                           role_code="RN"))
                s = t + C.AGENCY_LEAD_DAYS
                e = s + C.AGENCY_CONTRACT_WEEKS * 7 - 1
                n_ext = 0
                while rng.random() < C.AGENCY_EXTENSION_PROB and n_ext < 3:
                    n_ext += 1
                segs = [(s + i * C.AGENCY_CONTRACT_WEEKS * 7, e + i * C.AGENCY_CONTRACT_WEEKS * 7)
                        for i in range(n_ext + 1)]
                for i, (ss, ee) in enumerate(segs):
                    if ss > END:
                        break
                    contracts.append(dict(contract_id=f"AC{ctr:05d}-{i}", agency_worker_id=awid,
                                          unit_id=u, start_date=d(ss), end_date=d(min(ee, END + 365)),
                                          extension_no=i, weekly_hours=C.RN_WEEKLY_HOURS_AT_1FTE))
                    agency_cap[ss:ee + 1] += daily_hours_per_fte
                active_contracts.append((s, segs[-1][1], awid))
        gap = max(0.0, required[t] - available[t])
        staff = min(required[t], available[t])
        ot_share = C.OVERTIME_SHARE_OF_GAP if books_agency else C.OVERTIME_SHARE_OF_GAP_NO_AGENCY
        ot = min(gap * rng.uniform(*ot_share), required[t] * C.OVERTIME_CAP_SHARE_OF_REQUIRED)
        resid = gap - ot
        residual_hist[t] = resid
        ag = min(resid, agency_cap[t] * rng.uniform(0.92, 1.0))
        unfilled = resid - ag
        staffing_rows.append(dict(unit_id=u, date=dates[t].isoformat(), required_rn_hours=round(required[t], 1),
                                  staff_rn_hours=round(staff, 1), overtime_rn_hours=round(ot, 1),
                                  agency_rn_hours=round(ag, 1), unfilled_rn_hours=round(unfilled, 1),
                                  agency_rn_hours_scheduled=round(agency_cap[t], 1),
                                  staff_rn_fte_on_unit=round(fte_series[t], 2)))
staffing = pd.DataFrame(staffing_rows)
contracts = pd.DataFrame(contracts)
agency_workers = pd.DataFrame(agency_workers)

first_contract = contracts[contracts.extension_no == 0].drop_duplicates("agency_worker_id")
for _, r in first_contract.iterrows():
    sd = di(r.start_date)
    days = int(round(float(gamma_mean_sd(*C.PROFICIENCY_DAYS["agency"]))))
    if U[r.unit_id]["unit_name"] in SPECIALTY_NAMES:
        days = int(round(days * C.PROFICIENCY_SPECIALTY_MULTIPLIER))
    reached = sd + days <= END
    proficiency.append(dict(subject_type="agency", subject_id=r.agency_worker_id, unit_id=r.unit_id,
                            pathway="agency", start_date=r.start_date,
                            proficient_date=d(sd + days) if reached else None,
                            days_to_proficiency=days if reached else None, censored=not reached))

cost_rows = []
for k, v in C.COSTS.items():
    if isinstance(v, dict):
        for y, val in v.items():
            cost_rows.append(dict(assumption=k, year=y, value=val))
    else:
        cost_rows.append(dict(assumption=k, year=None, value=v))
cost_assumptions = pd.DataFrame(cost_rows)
BASIS = {"staff_rn_wage_per_hour_worked": "BLS ECEC Dec 2024 (2024); scaled about 4%/yr for 2023 and 2025",
         "benefits_load_on_wages_pct": "BLS ECEC Dec 2024, RNs in private hospitals",
         "overtime_multiplier": "FLSA minimum overtime premium",
         "agency_rn_bill_rate": "SIA/NATHO Travel Nurse Benchmarking Survey, national aggregate",
         "cost_per_rn_turnover": "NSI National Health Care Retention & RN Staffing Report (2025, 2026)",
         "agency_orientation_cost_per_contract": "Invented for illustration"}
cost_assumptions["basis"] = cost_assumptions.assumption.map(BASIS)

# ---------------------------------------------------------------------------
# 5. HR feed runs and LMS users
# ---------------------------------------------------------------------------
fail_days = set(range(di(C.HR_FEED_PLANTED_OUTAGE[0]), di(C.HR_FEED_PLANTED_OUTAGE[1]) + 1))
fail_days |= set(int(x) for x in rng.choice(ndays, C.HR_FEED_RANDOM_FAILURES, replace=False))


def next_success(day):
    t = day + 1
    while t in fail_days:
        t += 1
    return t


lms_users = []
lms_by_employee = {}
lms_by_person = {}
lu_counter = 0
usernames = set()


def make_username(first, last):
    base = f"{first[0]}{last}".lower()
    name = base
    n = 1
    while name in usernames:
        n += 1
        name = f"{base}{n}"
    usernames.add(name)
    return name


def add_lms_user(**kw):
    global lu_counter
    lu_counter += 1
    lid = f"L{lu_counter:06d}"
    row = dict(lms_user_id=lid, username=None, email=None, first_name=None, last_name=None,
               hr_employee_id=None, external_id=None, user_source=None, unit_id=None,
               created_date=None, deactivated_date=None, status="active")
    row.update(kw)
    lms_users.append(row)
    return lid


for eid in sorted(workers):
    w = workers[eid]
    p = persons[w["person_id"]]
    created = w["hire_day"] if w["hire_day"] < 0 else next_success(w["hire_day"] - 1)
    deact = None
    if w["term_day"] is not None:
        deact = next_success(w["term_day"])
        if rng.random() < C.FEED_DEACTIVATION_LONG_LAG_SHARE:
            deact += int(rng.integers(8, 41))
        if deact > END:
            deact = None
    reuse = None
    if w["rehire"] and rng.random() > C.REHIRE_NEW_ACCOUNT_SHARE:
        reuse = lms_by_employee.get(w["prior_employee_id"])
    if reuse:
        row = next(r for r in lms_users if r["lms_user_id"] == reuse)
        row.update(hr_employee_id=eid, unit_id=w["current_unit_id"], status="inactive" if deact else "active",
                   deactivated_date=d(deact))
        lms_by_employee[eid] = reuse
        w["lms_reactivated_day"] = created
        continue
    uname = make_username(p["first_name"], p["last_name"])
    lid = add_lms_user(username=uname, email=f"{uname}@tessalyhealth.example",
                       first_name=p["first_name"], last_name=p["last_name"], hr_employee_id=eid,
                       user_source="hr_feed", unit_id=w["current_unit_id"], created_date=d(created),
                       deactivated_date=d(deact), status="inactive" if deact else "active")
    lms_by_employee[eid] = lid
    lms_by_person.setdefault(w["person_id"], []).append(lid)
    w["lms_created_day"] = created

# Manual duplicate accounts for a small share of staff people
dup_candidates = [eid for eid, w in workers.items()
                  if (w["term_day"] is None or w["term_day"] > 400) and w["hire_day"] < END - 200]
dup_eids = set(rng.choice(dup_candidates, int(len(dup_candidates) * C.MANUAL_DUPLICATE_ACCOUNT_SHARE),
                          replace=False))
manual_dup = {}
for eid in sorted(dup_eids):
    w = workers[eid]
    p = persons[w["person_id"]]
    day = int(rng.integers(max(0, w["hire_day"]), min(END, w["term_day"] or END)))
    uname = make_username(p["first_name"], p["last_name"])
    lid = add_lms_user(username=uname, email=f"{uname}@tessalyhealth.example", first_name=p["first_name"],
                       last_name=p["last_name"], user_source="manual", created_date=d(day))
    manual_dup[eid] = (lid, day)

# Agency users
agency_lms = {}
for _, a in agency_workers.iterrows():
    c = contracts[contracts.agency_worker_id == a.agency_worker_id]
    start = di(c.start_date.min())
    end = di(c.end_date.max())
    uname = make_username(a.first_name, a.last_name)
    lid = add_lms_user(username=uname, email=f"{uname}@agency.example", first_name=a.first_name,
                       last_name=a.last_name, user_source="agency_manual",
                       external_id=a.agency_worker_id if rng.random() < C.AGENCY_EXTERNAL_ID_POPULATED else None,
                       unit_id=c.unit_id.iloc[-1], created_date=d(max(0, start - int(rng.integers(1, 11)))),
                       deactivated_date=d(end + int(rng.integers(0, 30))) if end + 30 < END else None,
                       status="inactive" if end + 30 < END else "active")
    agency_lms[a.agency_worker_id] = lid
for i in range(C.TEST_ACCOUNTS):
    add_lms_user(username=f"test.user{i + 1}", email=f"test.user{i + 1}@tessalyhealth.example",
                 first_name="Test", last_name=f"User{i + 1}", user_source="test",
                 created_date=d(int(rng.integers(0, END))))

feed_count = np.zeros(ndays + 40)
for w in workers.values():
    s0 = max(w["hire_day"], 0)
    e0 = END if w["term_day"] is None else min(END, w["term_day"] + 30)
    if s0 <= e0:
        feed_count[s0] += 1
        feed_count[e0 + 1] -= 1
feed_count = np.cumsum(feed_count)
feed_runs = []
for t in range(ndays):
    active = int(feed_count[t])
    if t in fail_days:
        feed_runs.append(dict(run_date=d(t), status="failed", rows_extracted=active, rows_loaded=0,
                              rows_rejected=0, run_minutes=int(rng.integers(1, 5))))
        continue
    rej = int(rng.poisson(0.3))
    feed_runs.append(dict(run_date=d(t), status="partial" if rej else "success", rows_extracted=active,
                          rows_loaded=active - rej, rows_rejected=rej, run_minutes=int(rng.integers(9, 25))))
feed_runs = pd.DataFrame(feed_runs)

# ---------------------------------------------------------------------------
# 6. Courses, enrollments, attempts, exemptions, certifications
# ---------------------------------------------------------------------------
course_rows = []
AC = [("AC-01", "Code of Conduct"), ("AC-02", "Information Security Awareness"),
      ("AC-03", "Workplace Safety"), ("AC-04", "Fire and Emergency Preparedness"),
      ("AC-05", "Respectful Workplace")]
for fam, title in AC:
    for y in YEARS:
        course_rows.append(dict(course_id=f"{fam}-{y}", course_family_id=fam, title=f"{title} {y}",
                                category="annual_compliance", catalog_priority="Required",
                                delivery="elearning", version_year=y, recurrence_months=12,
                                owner_role="Compliance Office", last_reviewed=f"{y - 1}-11-15",
                                retired_date=f"{y + 1}-01-31" if y < YEARS[-1] else None))
CERTS = {
    "CERT-LS": ("Role Certification: Life Support Renewal", 24, {"RN", "LPN", "RSP", "NMGR"}),
    "CERT-EQ": ("Role Certification: Equipment Competency", 12, {"RN", "LPN", "NA", "IMG", "LAB", "RSP", "SPD"}),
    "CERT-SU": ("Role Certification: Specialty Unit Competency", 24, {"RN"}),
    "CERT-HZ": ("Role Certification: Hazardous Materials Handling", 12, {"EVS", "FAC", "LAB", "SPD", "PHA"}),
}
for code, (title, months, _) in CERTS.items():
    course_rows.append(dict(course_id=code, course_family_id=code, title=title, category="certification_renewal",
                            catalog_priority="Required-Regulatory", delivery="blended", version_year=None,
                            recurrence_months=months, owner_role="Clinical Education", last_reviewed="2024-06-01",
                            retired_date=None))
ONB = [("ON-01", "New Employee Orientation", "all", 14),
       ("ON-02-NUR", "Role Onboarding: Nursing", "nursing", 30),
       ("ON-02-CLS", "Role Onboarding: Clinical Support", "clinical_support", 30),
       ("ON-02-ADM", "Role Onboarding: Administrative", "administrative", 30),
       ("ON-02-FAC", "Role Onboarding: Facilities and EVS", "facilities_evs", 30),
       ("ON-03", "Unit Orientation Checklist", "nursing", 60),
       ("AG-01", "Agency Clinician Orientation", "agency", 0)]
for cid, title, aud, due in ONB:
    course_rows.append(dict(course_id=cid, course_family_id=cid[:5] if cid.startswith("ON-02") else cid,
                            title=title, category="onboarding", catalog_priority="Required",
                            delivery="elearning" if cid != "ON-03" else "checklist", version_year=None,
                            recurrence_months=None, owner_role="Learning Operations" if cid != "ON-03" else None,
                            last_reviewed="2022-09-01", retired_date=None))
course_rows.append(dict(course_id="NR-01", course_family_id="NR-01", title="First-Year Nurse Residency",
                        category="residency", catalog_priority="Required", delivery="ilt_series",
                        version_year=None, recurrence_months=None, owner_role="Clinical Education",
                        last_reviewed="2024-01-10", retired_date=None))
for cid, title, pri, owner, rev in (("OP-01", "Leading Through Change", "Recommended", "Learning Operations", "2023-02-01"),
                                    ("OP-02", "Spreadsheet Basics", "Optional", None, "2019-05-01"),
                                    ("OP-03", "Preceptor Skills", "Recommended", "Clinical Education", "2021-03-15")):
    course_rows.append(dict(course_id=cid, course_family_id=cid, title=title, category="elective",
                            catalog_priority=pri, delivery="elearning", version_year=None, recurrence_months=None,
                            owner_role=owner, last_reviewed=rev, retired_date=None))
courses = pd.DataFrame(course_rows)
CPRI = dict(zip(courses.course_id, courses.catalog_priority))

enrollments, attempts, exemptions, certs = [], [], [], []
en_counter = 0
at_counter = 0
person_prop = {p: rng.normal(0, C.PERSON_PROPENSITY_SD) for p in persons}
unit_prop = {u: rng.normal(0, C.UNIT_PROPENSITY_SD) for u in U}


def propensity(eid, unit_id):
    p = person_prop[workers[eid]["person_id"]] + unit_prop[unit_id]
    if U[unit_id]["turnover_tier"] == "high":
        p += C.HIGH_TIER_PROPENSITY_SHIFT
    return p


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def logit(p):
    return math.log(p / (1 - p))


def unit_on(eid, day):
    for h in hist_by_emp[eid]:
        if h["start_day"] <= day and (h["end_day"] is None or h["end_day"] >= day):
            return h["unit_id"]
    return workers[eid]["current_unit_id"]


hist_by_emp = {}
for h in history:
    hist_by_emp.setdefault(h["employee_id"], []).append(h)


def add_attempts(en_id, lid, cid, start_day, pass_day, delivery="elearning"):
    """Record attempts ending in a pass on pass_day (with possible failed attempts first)."""
    global at_counter
    rows = []
    n = 1
    if delivery == "elearning" and rng.random() < C.ASSESSMENT_FAIL_RATE:
        fail_day = max(start_day, pass_day - int(rng.integers(0, 4)))
        rows.append((fail_day, "failed", int(rng.integers(50, 80))))
        n += 1
        if rng.random() < C.RETAKE_FAIL_RATE:
            rows.append((fail_day, "failed", int(rng.integers(50, 80))))
    rows.append((pass_day, "passed", int(rng.integers(80, 101)) if delivery == "elearning" else None))
    for i, (dd, res, sc) in enumerate(rows):
        at_counter += 1
        attempts.append(dict(attempt_id=f"AT{at_counter:07d}", enrollment_id=en_id, lms_user_id=lid,
                             course_id=cid, attempt_no=i + 1, started_at=d(dd), finished_at=d(dd),
                             result=res, score=sc))


def add_enrollment(lid, cid, assign_day, due_day, rule, cycle, done_day, stop_day, etype="assigned",
                   priority=None, delivery="elearning", eid=None):
    """Create an enrollment; done_day is when the learner would finish if still active."""
    global en_counter, at_counter
    en_counter += 1
    en_id = f"EN{en_counter:07d}"
    status, status_day, comp = "not_started", assign_day, None
    if done_day is not None and done_day <= END and (stop_day is None or done_day <= stop_day):
        status, status_day, comp = "completed", done_day, done_day
        add_attempts(en_id, lid, cid, assign_day, done_day, delivery)
    else:
        if rng.random() < 0.3 and delivery == "elearning":
            at_counter += 1
            sday = min(assign_day + int(rng.integers(0, 30)), END)
            attempts.append(dict(attempt_id=f"AT{at_counter:07d}", enrollment_id=en_id, lms_user_id=lid,
                                 course_id=cid, attempt_no=1, started_at=d(sday), finished_at=None,
                                 result="incomplete", score=None))
            status, status_day = "in_progress", sday
        if stop_day is not None and stop_day <= END and rng.random() < C.CANCEL_ON_TERMINATION_SHARE:
            status, status_day = "cancelled", stop_day + int(rng.integers(1, 15))
    enrollments.append(dict(enrollment_id=en_id, lms_user_id=lid, course_id=cid, enrollment_type=etype,
                            assignment_rule=rule, priority_label=priority or CPRI[cid], cycle_year=cycle,
                            assigned_date=d(assign_day), due_date=d(due_day), status=status,
                            status_date=d(min(status_day, END)), completion_date=d(comp)))
    return en_id


def draw_done(assign_day, due_day, prop, base=C.CAMPAIGN_ON_TIME_BASE):
    p_on = sigmoid(logit(base) + prop)
    r = rng.random()
    span = max(1, due_day - assign_day)
    if r < p_on:
        if rng.random() < 0.45:
            return assign_day + int(rng.integers(0, min(14, span) + 1))
        return assign_day + int(round(span * (1 - rng.beta(1.2, 3))))
    if rng.random() < C.CAMPAIGN_LATE_SHARE_OF_REST:
        return due_day + 1 + int(rng.exponential(21))
    return None


def employed(w, day):
    return w["hire_day"] <= day and (w["term_day"] is None or w["term_day"] >= day)


def lms_for(eid):
    return lms_by_employee[eid]


ex_counter = 0
reload_dupes = []

# 6a. Annual compliance campaigns + new-hire compliance assignments
for y in YEARS:
    a_day, due = ymd(y, C.CAMPAIGN_ASSIGN), ymd(y, C.CAMPAIGN_DUE)
    for eid, w in workers.items():
        if not employed(w, a_day):
            continue
        lid = lms_for(eid)
        unit = unit_on(eid, a_day)
        prop = propensity(eid, unit)
        base_done = draw_done(a_day, due, prop)
        stop = w["term_day"]
        leave = rng.random() < C.LEAVE_EXEMPTION_RATE
        if leave:
            ex_counter += 1
            g = a_day + int(rng.integers(0, 30))
            exemptions.append(dict(exemption_id=f"EX{ex_counter:06d}", lms_user_id=lid, course_family_id="AC-ALL",
                                   cycle_year=y, reason="leave_of_absence", granted_date=d(g),
                                   expires_date=d(g + 90), granted_by_role="Learning Operations"))
            base_done = (g + 90 + int(rng.integers(1, 40))) if rng.random() < 0.5 else None
        redirect = eid in manual_dup and manual_dup[eid][1] <= a_day + 60 and not w.get("dup_used")
        if redirect:
            w["dup_used"] = True
        for fam, _ in AC:
            cid = f"{fam}-{y}"
            done = None if base_done is None else base_done + int(rng.integers(0, 4))
            if done is not None and rng.random() < C.CAMPAIGN_SKIP_ONE_MODULE:
                done = None
            if fam == "AC-03" and rng.random() < C.EQUIVALENT_CREDIT_RATE:
                ex_counter += 1
                exemptions.append(dict(exemption_id=f"EX{ex_counter:06d}", lms_user_id=lid, course_family_id="AC-03",
                                       cycle_year=y, reason="equivalent_credit", granted_date=d(a_day + int(rng.integers(0, 40))),
                                       expires_date=None, granted_by_role="Compliance Office"))
                done = None
            pri = None
            if y == 2025 and fam == "AC-05" and fac_group[U[unit]["facility_id"]] == "Clinics":
                pri = "Recommended"  # planted: bulk-load priority label error
            if redirect:
                add_enrollment(lid, cid, a_day, due, "annual_campaign", y, None, stop, priority=pri)
                mlid, mday = manual_dup[eid]
                mdone = None if done is None else max(done, mday)
                add_enrollment(mlid, cid, max(a_day, mday), due, "manual_roster", y, mdone, stop, priority="Required")
            else:
                en = add_enrollment(lid, cid, a_day, due, "annual_campaign", y, done, stop, priority=pri)
                if y == 2024 and fam == "AC-04" and U[unit]["facility_id"] == "FAC-H2":
                    reload_dupes.append((lid, cid, a_day, due, stop))
    # new-hire compliance
    for eid, w in workers.items():
        h = w["hire_day"]
        if not (ymd(y, C.NEW_HIRE_COMPLIANCE_FROM) <= h <= ymd(y, "12-31")) or h > END:
            continue
        lid = lms_for(eid)
        prop = propensity(eid, w["hire_unit_id"])
        due_h = h + C.NEW_HIRE_COMPLIANCE_DUE_DAYS
        base_done = draw_done(h, due_h, prop)
        for fam, _ in AC:
            done = None if base_done is None else base_done + int(rng.integers(0, 3))
            add_enrollment(lid, f"{fam}-{y}", h, due_h, "new_hire", y, done, w["term_day"])

# planted: 2024 AC-04 duplicate reload at Community North (never completed)
for lid, cid, a_day, due, stop in reload_dupes:
    add_enrollment(lid, cid, a_day, due, "annual_campaign", 2024, None, None)

# 6b. Onboarding
for eid, w in workers.items():
    if not w["in_window_hire"]:
        continue
    h = w["hire_day"]
    lid = lms_for(eid)
    fam = ROLE_FAMILY[w["role_code"]]
    prop = propensity(eid, w["hire_unit_id"])
    add_enrollment(lid, "ON-01", h, h + 14, "new_hire", None, draw_done(h, h + 14, prop, 0.9), w["term_day"])
    code = {"nursing": "ON-02-NUR", "clinical_support": "ON-02-CLS", "administrative": "ON-02-ADM",
            "facilities_evs": "ON-02-FAC"}[fam]
    ob = None if w["onboarding_days"] is None else h + w["onboarding_days"]
    add_enrollment(lid, code, h, h + 30, "new_hire", None, ob, w["term_day"])
    if fam == "nursing" and w["role_code"] != "NMGR":
        add_enrollment(lid, "ON-03", h, h + 60, "new_hire", None, draw_done(h, h + 60, prop, 0.75),
                       w["term_day"], delivery="checklist")
    if w["new_grad"]:
        cday = w.get("residency_complete_day")
        add_enrollment(lid, "NR-01", h, h + 400, "residency", None, cday, w["term_day"], delivery="ilt")

# 6c. Certifications
cert_counter = 0


def applicable_certs(role, unit_id):
    out = [c for c, (_, _, rset) in CERTS.items() if role in rset and c != "CERT-SU"]
    if role == "RN" and U[unit_id]["specialty_cert_required"]:
        out.append("CERT-SU")
    return out


for eid, w in workers.items():
    lid = lms_for(eid)
    for h in hist_by_emp[eid]:
        unit = h["unit_id"]
        seg_start = max(h["start_day"], 0)
        seg_end = min(h["end_day"] if h["end_day"] is not None else END, END)
        if seg_start > seg_end:
            continue
        for code in applicable_certs(w["role_code"], unit):
            if code in w.setdefault("certs_done", set()) and code != "CERT-SU":
                continue
            w["certs_done"].add(code)
            months = CERTS[code][1]
            cycle = int(months * 30.4)
            stop = w["term_day"]
            prop = propensity(eid, unit)
            if h["change_reason"] == "hire" and not w["in_window_hire"]:
                exp = int(rng.integers(0, cycle))
                issued = exp - cycle
                src = "prior_record"
            elif w["new_grad"] or h["change_reason"] == "transfer":
                a = seg_start
                done = draw_done(a, a + 90, prop, 0.85)
                en = add_enrollment(lid, code, a, a + 90, "role_certification", None, done, stop, priority=None)
                if done is None or done > END or (stop and done > stop):
                    continue
                issued, exp, src = done, done + cycle, "lms_completion"
            else:
                issued = seg_start - int(rng.integers(0, cycle - 60))
                exp, src = issued + cycle, "external_upload"
            cert_counter += 1
            certs.append(dict(cert_record_id=f"CR{cert_counter:07d}", employee_id=eid, lms_user_id=lid,
                              cert_code=code, issued_date=d(issued), expires_date=d(exp), source=src))
            # renewals
            limit = seg_end if code == "CERT-SU" else END
            while True:
                a = exp - C.CERT_RENEWAL_LEAD_DAYS
                if a > END or a > limit or (stop is not None and a > stop):
                    break
                a = max(a, seg_start)
                r = rng.random()
                if r < C.CERT_ON_TIME:
                    done = a + int(round((exp - a) * (1 - rng.beta(1.2, 2.5))))
                elif r < C.CERT_ON_TIME + C.CERT_LATE:
                    done = exp + 1 + int(rng.exponential(15))
                else:
                    done = None
                add_enrollment(lid, code, a, exp, "role_certification", None, done, stop)
                if done is None or done > END or (stop is not None and done > stop):
                    break
                cert_counter += 1
                exp = done + cycle
                certs.append(dict(cert_record_id=f"CR{cert_counter:07d}", employee_id=eid, lms_user_id=lid,
                                  cert_code=code, issued_date=d(done), expires_date=d(exp), source="lms_completion"))

# 6d. Agency enrollments
for _, c in contracts[contracts.extension_no == 0].iterrows():
    lid = agency_lms[c.agency_worker_id]
    s = di(c.start_date)
    if s > END:
        continue
    y = (D0 + timedelta(days=s)).year
    prop = rng.normal(0.3, 0.5)
    add_enrollment(lid, "AG-01", s - 3, s, "agency_contract", None, draw_done(s - 3, s, prop, 0.9), None)
    for fam in ("AC-01", "AC-02"):
        add_enrollment(lid, f"{fam}-{y}", s, s + 7, "agency_contract", y, draw_done(s, s + 7, prop, 0.85), None)

# 6e. Electives
for y in YEARS:
    for eid, w in workers.items():
        mid = ymd(y, "06-30")
        if not employed(w, mid):
            continue
        lid = lms_for(eid)
        if rng.random() < C.SELF_ENROLL_RATE:
            a = ymd(y, "01-01") + int(rng.integers(0, 365))
            if a <= END and employed(w, a):
                done = a + int(rng.integers(1, 30)) if rng.random() < 0.55 else None
                add_enrollment(lid, "OP-02", a, a + 365, "self_enrollment", None, done, w["term_day"], etype="self")
        if w["role_code"] == "RN" and mid - w["hire_day"] > 730 and rng.random() < C.PRECEPTOR_ASSIGN_RATE:
            a = ymd(y, "03-01") + int(rng.integers(0, 120))
            done = a + int(rng.integers(5, 60)) if rng.random() < 0.7 else None
            add_enrollment(lid, "OP-03", a, a + 60, "manager_assigned", None, done, w["term_day"])
        if w["role_code"] in ("NMGR", "DMGR") and y == 2024:
            a, due = ymd(2024, "03-01"), ymd(2024, "06-30")
            add_enrollment(lid, "OP-01", a, due, "manager_assigned", None,
                           draw_done(a, due, 0.0, 0.7), w["term_day"])

# Test accounts complete a few things
for r in [x for x in lms_users if x["user_source"] == "test"]:
    c0 = di(r["created_date"])
    for cid in rng.choice([f"AC-0{i}-{YEARS[-1]}" for i in range(1, 6)], 3, replace=False):
        add_enrollment(r["lms_user_id"], str(cid), c0, c0 + 30, "manual_roster", YEARS[-1],
                       min(END, c0 + int(rng.integers(0, 5))), None)

enrollments = pd.DataFrame(enrollments)
attempts = pd.DataFrame(attempts)

# 6f. Data-quality defects
planted_issues = []
# old-version completions in latest year (Information Security)
ly = YEARS[-1]
mask = (enrollments.course_id == f"AC-02-{ly}") & (enrollments.status == "completed") & \
       (enrollments.assignment_rule == "annual_campaign")
pick = enrollments[mask].sample(frac=C.DQ_OLD_VERSION_COMPLETION, random_state=C.SEED).index
new_rows = []
for i in pick:
    r = enrollments.loc[i]
    en_counter += 1
    new_id = f"EN{en_counter:07d}"
    new_rows.append(dict(enrollment_id=new_id, lms_user_id=r.lms_user_id, course_id=f"AC-02-{ly - 1}",
                         enrollment_type="self", assignment_rule="self_enrollment", priority_label="Required",
                         cycle_year=ly - 1, assigned_date=r.completion_date, due_date=None, status="completed",
                         status_date=r.completion_date, completion_date=r.completion_date))
    m = attempts.enrollment_id == r.enrollment_id
    attempts.loc[m, "course_id"] = f"AC-02-{ly - 1}"
    attempts.loc[m, "enrollment_id"] = new_id
    enrollments.loc[i, ["status", "completion_date", "status_date"]] = ["not_started", None, r.assigned_date]
enrollments = pd.concat([enrollments, pd.DataFrame(new_rows)], ignore_index=True)
planted_issues.append(dict(issue_id="DQ-01", table="enrollments", description=f"{len(pick)} learners completed the prior-year version of Information Security in {ly} instead of the current version", rows_affected=len(pick)))

passed = attempts[attempts.result == "passed"]
dup = passed.sample(frac=C.DQ_DUPLICATE_ATTEMPT_ROWS, random_state=1).copy()
dup["attempt_id"] = [f"AT{at_counter + i + 1:07d}" for i in range(len(dup))]
at_counter += len(dup)
attempts = pd.concat([attempts, dup], ignore_index=True)
planted_issues.append(dict(issue_id="DQ-02", table="attempts", description="Exact duplicate passed-attempt rows (new attempt_id, same timestamp)", rows_affected=len(dup)))

comp = enrollments[enrollments.status == "completed"]
noatt = comp.sample(frac=C.DQ_COMPLETED_WITHOUT_ATTEMPT, random_state=2).enrollment_id
attempts = attempts[~attempts.enrollment_id.isin(noatt)]
planted_issues.append(dict(issue_id="DQ-03", table="enrollments", description="Enrollment marked completed with no attempt record", rows_affected=len(noatt)))

bad = enrollments[enrollments.due_date.notna()].sample(frac=C.DQ_DUE_BEFORE_ASSIGNED, random_state=3).index
enrollments.loc[bad, "due_date"] = [d(di(a) - int(rng.integers(1, 365))) for a in enrollments.loc[bad, "assigned_date"]]
planted_issues.append(dict(issue_id="DQ-04", table="enrollments", description="Due date earlier than assigned date", rows_affected=len(bad)))

planted_issues += [
    dict(issue_id="DQ-05", table="enrollments", description="2024 Fire and Emergency Preparedness campaign reloaded at Community North; duplicate enrollments never completed", rows_affected=len(reload_dupes)),
    dict(issue_id="DQ-06", table="enrollments", description="2025 Respectful Workplace enrollments at Clinics carry priority_label 'Recommended' though the course is Required", rows_affected=int(((enrollments.course_id == "AC-05-2025") & (enrollments.priority_label == "Recommended")).sum())),
    dict(issue_id="DQ-07", table="lms_users", description="Manual duplicate accounts for staff; one compliance cycle recorded on the duplicate", rows_affected=len(manual_dup)),
    dict(issue_id="DQ-08", table="lms_users", description="Test accounts with completions", rows_affected=C.TEST_ACCOUNTS),
    dict(issue_id="DQ-09", table="courses", description="Courses with no owner_role (ON-03, OP-02); OP-02 not reviewed since 2019", rows_affected=2),
    dict(issue_id="DQ-10", table="lms_users", description="Agency accounts missing external_id (cannot link to agency roster)", rows_affected=sum(1 for r in lms_users if r["user_source"] == "agency_manual" and not r["external_id"])),
]

exemptions = pd.DataFrame(exemptions)
certs = pd.DataFrame(certs)
lms_users_df = pd.DataFrame(lms_users)

# ---------------------------------------------------------------------------
# 7. Governed reporting: catalog, lineage, published scorecard, BI access
# ---------------------------------------------------------------------------
reports = [
    ("RPT-001", "Executive Compliance Scorecard", "Learning Operations", "Executive team", "monthly", "facility-month", "active", 41),
    ("RPT-002", "Compliance Scorecard (Legacy)", "Learning Operations", "Executive team", "monthly", "facility-month", "duplicate", 3),
    ("RPT-003", "Overdue Training by Unit", "Learning Operations", "Unit managers", "weekly", "unit-week", "active", 212),
    ("RPT-004", "Overdue Training by Manager", "Human Resources", "Department managers", "weekly", "manager-week", "active", 64),
    ("RPT-005", "Certification Expiry 60-Day Outlook", "Clinical Education", "Nurse managers", "weekly", "person", "active", 180),
    ("RPT-006", "Certification Lapses", "Clinical Education", "Nursing leadership", "monthly", "unit-month", "active", 22),
    ("RPT-007", "New Hire Onboarding Status", "Learning Operations", "Unit managers", "weekly", "person", "active", 95),
    ("RPT-008", "Onboarding Completion Rates", "Human Resources", "HR leadership", "monthly", "facility-month", "active", 8),
    ("RPT-009", "Residency Attendance", "Clinical Education", "Residency coordinators", "monthly", "person-session", "active", 30),
    ("RPT-010", "Agency Utilization by Unit", "Nursing Finance", "Nursing leadership", "monthly", "unit-month", "active", 27),
    ("RPT-011", "Agency Spend Summary", "Finance", "Executive team", "monthly", "facility-month", "active", 12),
    ("RPT-012", "Agency Hours (Old Format)", "Nursing Finance", "Nursing leadership", "monthly", "unit-month", "duplicate", 1),
    ("RPT-013", "Annual Compliance Raw Extract", "Learning Operations", "Analysts", "daily", "enrollment", "active", 15),
    ("RPT-014", "Course Catalog Inventory", "Learning Operations", "LMS administrators", "quarterly", "course", "active", 4),
    ("RPT-015", "Elective Course Usage", "Learning Operations", "Learning Operations", "quarterly", "course-quarter", "active", 0),
    ("RPT-016", "Turnover by Unit", "Human Resources", "HR leadership", "monthly", "unit-month", "active", 19),
    ("RPT-017", "First-Year Turnover", "Human Resources", "Nursing leadership", "quarterly", "cohort-quarter", "active", 9),
    ("RPT-018", "Time to Proficiency", "Clinical Education", "Nursing leadership", "quarterly", "person", "active", 6),
    ("RPT-019", "Training Hours per FTE", "Learning Operations", "HR leadership", "quarterly", "facility-quarter", "active", 0),
    ("RPT-020", "LMS Login Activity", "Information Technology", "LMS administrators", "monthly", "user-month", "active", 2),
    ("RPT-021", "Compliance by Job Role", "Compliance Office", "Compliance Office", "monthly", "role-month", "active", 11),
    ("RPT-022", "Compliance by Job Role v2", "Compliance Office", "Compliance Office", "monthly", "role-month", "duplicate", 5),
]
report_catalog = pd.DataFrame(reports, columns=["report_id", "report_name", "owner_department", "primary_audience",
                                                "refresh_frequency", "grain", "catalog_status", "views_last_90_days"])
lineage = pd.DataFrame([
    ("RPT-001", 1, "HR system", "hr_feed_runs (nightly extract)", "Nightly extract of active and recently terminated staff", "Row count extracted vs. loaded"),
    ("RPT-001", 2, "hr_feed_runs", "lms_users", "Create, update, and deactivate LMS accounts from the feed", "Rejected rows reviewed next business day"),
    ("RPT-001", 3, "LMS", "warehouse.stg_enrollments", "Nightly copy of enrollments and attempts", "Source vs. staging row counts"),
    ("RPT-001", 4, "warehouse.stg_enrollments", "warehouse.fct_compliance_month", "Filter annual compliance courses for the cycle year; join user to facility; month-end snapshot", "None (gap)"),
    ("RPT-001", 5, "warehouse.fct_compliance_month", "BI: Executive Compliance Scorecard", "Numerator = status completed by month end; denominator = all enrollments assigned by month end", "None (gap)"),
], columns=["report_id", "step", "source", "target", "transformation", "control_in_place"])

lu_fac = {r["lms_user_id"]: (fac_group[U[r["unit_id"]]["facility_id"]] if r["unit_id"] else "Unassigned",
                             r["user_source"]) for r in lms_users}
ac = enrollments[enrollments.course_id.str.startswith("AC-")].copy()
ac["fgroup"] = ac.lms_user_id.map(lambda x: lu_fac[x][0])
ac["src"] = ac.lms_user_id.map(lambda x: lu_fac[x][1])
ac["a"] = pd.to_datetime(ac.assigned_date)
ac["c"] = pd.to_datetime(ac.completion_date)
ac["due"] = pd.to_datetime(ac.due_date)


def scorecard(month_end, sources=("hr_feed",), as_of=None):
    as_of = as_of or month_end
    y = month_end.year
    s = ac[(ac.cycle_year == y) & (ac.src.isin(sources)) & (ac.a <= as_of) & (ac.fgroup != "Unassigned")]
    g = s.groupby("fgroup")
    out = pd.DataFrame({"denominator": g.size(),
                        "numerator": g.apply(lambda x: ((x.status == "completed") & (x.c <= as_of)).sum()),
                        "overdue": g.apply(lambda x: ((x.due <= as_of) & ~((x.status == "completed") & (x.c <= as_of))).sum())})
    return out


published = []
month_ends = pd.date_range(f"{YEARS[0]}-02-01", C.WINDOW_END, freq="ME")
for me in month_ends:
    tag = None
    if me.strftime("%Y-%m") == "2024-08":
        sc = scorecard(me, as_of=me - pd.Timedelta(days=4))
        tag = "PI-01"
    elif me.strftime("%Y-%m") == "2025-10":
        sc = scorecard(me)
        sc_ag = scorecard(me, sources=("hr_feed", "agency_manual"))
        sc.loc["Flagship Hospital"] = sc_ag.loc["Flagship Hospital"]
        tag = "PI-03"
    else:
        sc = scorecard(me)
    if me.strftime("%Y-%m") == "2025-03":
        s = ac[(ac.cycle_year == 2025) & (ac.src == "hr_feed") & (ac.fgroup == "Community North") &
               (ac.status == "completed") & (ac.c.dt.strftime("%Y-%m") == "2025-03")]
        sc.loc["Community North", "numerator"] += len(s)
        tag = "PI-02"
    for fg, r in sc.iterrows():
        published.append(dict(report_id="RPT-001", report_month=me.strftime("%Y-%m"), facility_group=fg,
                              numerator=int(r.numerator), denominator=int(r.denominator),
                              completion_rate_pct=round(100 * r.numerator / r.denominator, 1) if r.denominator else None,
                              overdue_enrollments=int(r.overdue),
                              published_date=(me + pd.Timedelta(days=int(rng.integers(3, 8)))).date().isoformat()))
published = pd.DataFrame(published)
planted_issues += [
    dict(issue_id="PI-01", table="report_published_values", description="2024-08 scorecard built from data 4 days stale (HR feed outage 2024-08-27 to 08-29 delayed the load); all facilities", rows_affected=int((published.report_month == "2024-08").sum())),
    dict(issue_id="PI-02", table="report_published_values", description="2025-03 Community North numerator double-counts March completions (attempts loaded twice)", rows_affected=1),
    dict(issue_id="PI-03", table="report_published_values", description="2025-10 Flagship Hospital includes agency accounts in numerator and denominator", rows_affected=1),
]

bi_roles = pd.DataFrame([
    ("BI-EXEC", "Executive viewer", "system", False),
    ("BI-FAC", "Facility leader", "facility", False),
    ("BI-UNIT", "Unit or department manager", "unit", True),
    ("BI-ANALYST", "Learning analyst", "system", True),
    ("BI-ANALYST-AGG", "Reporting analyst (aggregate only)", "system", False),
], columns=["bi_role", "description", "allowed_scope", "person_level_detail"])
bi_users = []
mgrs = [w for w in workers.values() if w["role_code"] in ("NMGR", "DMGR")]
for i, w in enumerate(mgrs):
    bi_users.append(dict(bi_user_id=f"BIU{i + 1:04d}", employee_id=w["employee_id"], bi_role="BI-UNIT",
                         scope_type="unit", scope_value=w["current_unit_id"], person_level_detail=True,
                         granted_date=d(max(0, w["hire_day"]) + 7), revoked_date=d(w["term_day"] + 2) if w["term_day"] else None))
n = len(bi_users)
staff_admin = [w for w in workers.values() if w["role_code"] == "ADM" and w["term_day"] is None]
for j, (role, scope_type, scope_val, pld) in enumerate(
        [("BI-EXEC", "system", "ALL", False)] * 6 + [("BI-FAC", "facility", f, False) for f in ("FAC-H1", "FAC-H2", "FAC-H3", "FAC-HH")]
        + [("BI-ANALYST", "system", "ALL", True)] * 3 + [("BI-ANALYST-AGG", "system", "ALL", False)] * 3):
    w = staff_admin[j]
    bi_users.append(dict(bi_user_id=f"BIU{n + j + 1:04d}", employee_id=w["employee_id"], bi_role=role, scope_type=scope_type,
                         scope_value=scope_val, person_level_detail=pld, granted_date=d(max(0, w["hire_day"]) + 7), revoked_date=None))
bi_users = pd.DataFrame(bi_users)
# planted access issues
termed = bi_users[bi_users.revoked_date.notna()].index[:2]
bi_users.loc[termed, "revoked_date"] = None
um = bi_users[(bi_users.bi_role == "BI-UNIT") & bi_users.revoked_date.isna()].index[5]
bi_users.loc[um, ["scope_type", "scope_value"]] = ["system", "ALL"]
agg = bi_users[bi_users.bi_role == "BI-ANALYST-AGG"].index[0]
bi_users.loc[agg, "person_level_detail"] = True
planted_issues += [
    dict(issue_id="AX-01", table="bi_users", description="Terminated managers whose BI access was never revoked", rows_affected=2),
    dict(issue_id="AX-02", table="bi_users", description="Unit manager granted system-wide scope", rows_affected=1),
    dict(issue_id="AX-03", table="bi_users", description="Aggregate-only analyst role granted person-level detail", rows_affected=1),
]

# ---------------------------------------------------------------------------
# 8. Write output
# ---------------------------------------------------------------------------
def main(out):
    out = Path(out)
    gt = out.parent / "ground_truth"
    out.mkdir(parents=True, exist_ok=True)
    gt.mkdir(parents=True, exist_ok=True)
    emp = pd.DataFrame([dict(employee_id=w["employee_id"], person_id=w["person_id"], role_code=w["role_code"],
                             hire_unit_id=w["hire_unit_id"], current_unit_id=w["current_unit_id"], fte=w["fte"],
                             hire_date=d(w["hire_day"]), termination_date=d(w["term_day"]),
                             termination_type=w["term_type"], rehire_flag=w["rehire"],
                             prior_employee_id=w["prior_employee_id"], new_grad_flag=w["new_grad"])
                        for w in workers.values()])
    hist_out = hist.assign(start_date=hist.start_day.map(d), end_date=hist.end_day.map(d)) \
        .drop(columns=["start_day", "end_day"])
    tables = {
        "facilities": facilities, "units": units, "roles": roles,
        "persons": pd.DataFrame(persons.values()), "employees": emp, "employee_unit_history": hist_out,
        "residency_cohort_members": pd.DataFrame(residents), "residency_attendance": pd.DataFrame(attendance),
        "proficiency": pd.DataFrame(proficiency), "unit_staffing_daily": staffing,
        "agency_workers": agency_workers, "agency_contracts": contracts, "cost_assumptions": cost_assumptions,
        "hr_feed_runs": feed_runs, "lms_users": lms_users_df, "courses": courses, "enrollments": enrollments,
        "attempts": attempts, "exemptions": exemptions, "certifications": certs,
        "report_catalog": report_catalog, "report_lineage": lineage, "report_published_values": published,
        "bi_access_roles": bi_roles, "bi_users": bi_users,
    }
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
    pd.DataFrame(planted_issues).to_csv(gt / "planted_issues.csv", index=False)
    pd.DataFrame([dict(lms_user_id=lid, true_employee_id=eid, true_person_id=workers[eid]["person_id"])
                  for eid, (lid, _) in manual_dup.items()]).to_csv(gt / "manual_account_owners.csv", index=False)
    effects = pd.DataFrame([
        ("E-01", "Year-1 voluntary turnover hazard ratio, role onboarding finished within 30 days", C.HR_ONBOARDING_ON_TIME,
         "Confounded: on-time rate is lower on high-turnover units"),
        ("E-02", "Year-1 voluntary turnover hazard ratio, new-grad RN with attendance propensity >= 0.80", C.HR_RESIDENCY_HIGH_ATTENDER,
         "Completion requires surviving 12 months, so comparing completers to non-completers is biased (immortal time)"),
        ("E-03", "First-year voluntary hazard multiplier (all staff)", C.FIRST_YEAR_HAZARD_MULTIPLIER, "Applies before E-01 and E-02"),
        ("E-04", "Mean days to proficiency, new grad high vs. low attender", f"{C.PROFICIENCY_DAYS['new_grad_high_attender'][0]} vs {C.PROFICIENCY_DAYS['new_grad_low_attender'][0]}", "Times 1.2 on ICU, ED, Step-Down"),
    ], columns=["effect_id", "description", "true_value", "note"])
    effects.to_csv(gt / "planted_effects.csv", index=False)
    meta = dict(seed=C.SEED, window=[C.WINDOW_START, C.WINDOW_END],
                rows={k: int(len(v)) for k, v in tables.items()})
    (out / "manifest.json").write_text(json.dumps(meta, indent=2))
    for k, v in meta["rows"].items():
        print(f"{k:28s} {v:>9,}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    main(ap.parse_args().out)
