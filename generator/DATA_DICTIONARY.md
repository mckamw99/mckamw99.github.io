# Data dictionary

All tables are CSV in `data/`. Dates are ISO `YYYY-MM-DD`. Blank means null. Row counts are for seed 20261108 (see `data/manifest.json`). Case-study letters show which analysis uses the table.

## Organization

**facilities** (25) · all
`facility_id`, `facility_name`, `facility_type` (hospital_flagship, hospital_community, clinic, home_health, system_office), `facility_group` (the grouping used on the executive scorecard).

**units** (120) · all
`unit_id`, `unit_name`, `facility_id`, `unit_kind` (inpatient, clinic, home_health, admin, department), `department_type` (nursing, non_nursing), `turnover_tier` (high, medium, low; nursing only), `specialty_cert_required`, `budgeted_rn`, `budgeted_lpn`, `budgeted_na`.

**roles** (16) · all
`role_code`, `role_name`, `role_family` (nursing, clinical_support, administrative, facilities_evs), `licensed`.

## People and employment (HR side)

**persons** (6,284) · A, B
One row per human. `person_id`, `first_name`, `last_name`. A rehired person keeps the same `person_id`.

**employees** (6,387) · A, B, C
One row per employment spell. `employee_id`, `person_id`, `role_code`, `hire_unit_id`, `current_unit_id` (last unit), `fte`, `hire_date` (can be before the window), `termination_date`, `termination_type` (voluntary, involuntary), `rehire_flag`, `prior_employee_id`, `new_grad_flag`.

**employee_unit_history** (6,548) · A, B, C
`employee_id`, `unit_id`, `change_reason` (hire, rehire, transfer), `start_date`, `end_date` (blank = still there).

**hr_feed_runs** (1,096) · D
Nightly HR-to-LMS feed log. `run_date`, `status` (success, partial, failed), `rows_extracted`, `rows_loaded`, `rows_rejected`, `run_minutes`.

## Residency and proficiency

**residency_cohort_members** (197) · B
`employee_id`, `cohort_id` (NR-YYYY-MM), `cohort_start_date`, `sessions_attended`, `residency_completed`, `completion_date`.

**residency_attendance** (1,584) · B
One row per resident per session held while employed. `employee_id`, `cohort_id`, `session_no` (1–12), `session_date`, `attended`.

**proficiency** (1,081) · B, C
Inpatient staff RN hires in the window and first agency contracts. `subject_type` (staff, agency), `subject_id` (employee_id or agency_worker_id), `unit_id`, `pathway` (new_grad, experienced_hire, agency), `start_date`, `proficient_date`, `days_to_proficiency`, `censored` (left or window ended first).

## Staffing and agency

**unit_staffing_daily** (19,728) · C
One row per inpatient unit per day. `required_rn_hours`, `staff_rn_hours` (straight time), `overtime_rn_hours`, `agency_rn_hours` (worked), `unfilled_rn_hours`, `agency_rn_hours_scheduled` (contracted capacity, can exceed worked), `staff_rn_fte_on_unit`. Staff + overtime + agency + unfilled = required.

**agency_workers** (497) · C, A
`agency_worker_id`, `agency_name` (Agency A/B/C), `first_name`, `last_name`, `role_code`.

**agency_contracts** (634) · C
One row per 13-week segment. `contract_id`, `agency_worker_id`, `unit_id`, `start_date`, `end_date`, `extension_no` (0 = original), `weekly_hours`.

**cost_assumptions** (11) · C
`assumption`, `year`, `value`, `basis` (source of each figure; most are public benchmarks).

## Learning (LMS side)

**lms_users** (6,910) · A, D
`lms_user_id`, `username`, `email` (example domains), `first_name`, `last_name`, `hr_employee_id` (current link; blank on manual, agency and test accounts), `external_id` (agency ID, sometimes missing), `user_source` (hr_feed, manual, agency_manual, test), `unit_id` (last known), `created_date`, `deactivated_date`, `status`.

**courses** (30) · A
`course_id`, `course_family_id` (stable across yearly versions), `title`, `category` (annual_compliance, certification_renewal, onboarding, residency, elective), `catalog_priority` (Required, Required-Regulatory, Recommended, Optional), `delivery`, `version_year`, `recurrence_months`, `owner_role`, `last_reviewed`, `retired_date`.

**enrollments** (93,846) · A, B, D
One row per assignment or self-enrollment, as the LMS stores it. `enrollment_id`, `lms_user_id`, `course_id`, `enrollment_type` (assigned, self), `assignment_rule` (annual_campaign, new_hire, role_certification, residency, agency_contract, manager_assigned, self_enrollment, manual_roster), `priority_label` (as stamped on the enrollment; can disagree with the course), `cycle_year`, `assigned_date`, `due_date`, `status` (not_started, in_progress, completed, cancelled), `status_date`, `completion_date`. Enrollments for people who left usually stay open.

**attempts** (91,782) · A
`attempt_id`, `enrollment_id`, `lms_user_id`, `course_id`, `attempt_no`, `started_at`, `finished_at`, `result` (passed, failed, incomplete), `score` (blank for instructor-led and checklists).

**exemptions** (404) · A
`exemption_id`, `lms_user_id`, `course_family_id` (AC-ALL covers every annual module), `cycle_year`, `reason` (leave_of_absence, equivalent_credit), `granted_date`, `expires_date`, `granted_by_role`.

**certifications** (19,247) · A
`cert_record_id`, `employee_id`, `lms_user_id`, `cert_code`, `issued_date`, `expires_date`, `source` (prior_record, external_upload, lms_completion).

## Reporting and access

**report_catalog** (22) · D
`report_id`, `report_name`, `owner_department`, `primary_audience`, `refresh_frequency`, `grain`, `catalog_status` (active, duplicate), `views_last_90_days`.

**report_lineage** (5) · D
The executive scorecard's path from HR system to BI. `report_id`, `step`, `source`, `target`, `transformation`, `control_in_place`.

**report_published_values** (208) · D
What the executive scorecard showed each month. `report_id`, `report_month`, `facility_group`, `numerator`, `denominator`, `completion_rate_pct`, `overdue_enrollments`, `published_date`.

**bi_access_roles** (5) · D
`bi_role`, `description`, `allowed_scope`, `person_level_detail`.

**bi_users** (186) · D
`bi_user_id`, `employee_id`, `bi_role`, `scope_type`, `scope_value`, `person_level_detail`, `granted_date`, `revoked_date`.

## Answer key (`ground_truth/`)

**planted_effects.csv**: `effect_id`, `description`, `true_value`, `note`.
**planted_issues.csv**: `issue_id`, `table`, `description`, `rows_affected`.
