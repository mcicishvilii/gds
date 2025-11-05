print("=== DEBUG: Starting main M3_BIN decision flow ===")

scoring_bin = record.system.application.tbcbank.request.applicationdata.scoringbin
ism3_binclient = record.system.application.tbcbank.request.applicationdata.ism3_binclient
segment_group = record.system.application.tbcbank.response.checkresult.segmentgroup
apps = safe_get_node(record.system.application.tbcbank.request.applicants.applicant)
# Removed: decisions loop and related debug logic

print(f"DEBUG: scoring_bin = {scoring_bin}")
print(f"DEBUG: ism3_binclient = {ism3_binclient}")
print(f"DEBUG: segment_group = {segment_group}")
print(f"DEBUG: apps type = {type(apps)}, length = {len(apps) if hasattr(apps, '__len__') else 'N/A'}")

for i in range(len(apps)):
    print(f"\n--- DEBUG: Processing applicant index {i} ---")
    app = apps[i]
    print(f"DEBUG: Applicant object: {app}")

    try:
        bureau_grade = app.creditbureauinfo.creditrating.bureaugrade
        print(f"DEBUG: bureau_grade = {bureau_grade}")
    except Exception as e:
        print(f"ERROR: Could not retrieve bureau_grade for applicant {i}: {e}")
        bureau_grade = None

    # ========== STEP 2a ==========
    print(f"DEBUG: Checking STEP 2a conditions for applicant {i} ...")
    if (
        bureau_grade == "E3"
        and scoring_bin in [4, 5, 6, 7, 8]
        and ism3_binclient == GDS_FALSE
    ):
        print("DEBUG: STEP 2a triggered (E3 + scoring_bin 4-8 + ism3_binclient=FALSE)")
        add_decision_once(record, "D124", "High Risk", result="Decline")
        record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_FALSE
        print("DEBUG: Decision D124 (Decline) added and isapprovedm3_bin set to FALSE")
        continue

    # ========== STEP 2b ==========
    print(f"DEBUG: Checking STEP 2b conditions for applicant {i} ...")
    if bureau_grade == "E2" and scoring_bin in [5, 6, 7, 8]:
        print("DEBUG: STEP 2b triggered (E2 + scoring_bin 5-8)")

        if ism3_binclient == GDS_FALSE:
            print("DEBUG: ism3_binclient = FALSE → Decline case")
            add_decision_once(record, "D124", "High Risk", result="Decline")
            record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_FALSE
            continue

        if ism3_binclient == GDS_TRUE:
            print("DEBUG: ism3_binclient = TRUE → Investigating product_code & segment_group branches")
            if product_code != "CL_WS":
                print("DEBUG: product_code != CL_WS")
                if segment_group == OTHER:
                    print("DEBUG: segment_group == OTHER → Investigate")
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "I300", "Medium Risk", result="Investigate")

            if product_code == "CL_WS":
                print("DEBUG: product_code == CL_WS → checking job info")
                check_income_gel = app.jobs.checkincomegel
                print(f"DEBUG: check_income_gel = {check_income_gel}")

                job_count = 0
                jobinfos = safe_get_node(app.jobs.jobinfo)
                print(f"DEBUG: jobinfos = {jobinfos}")

                if jobinfos is None or jobinfos == []:
                    job_count = 0
                    print("DEBUG: No jobinfo found → job_count = 0")
                else:
                    job_count = len(jobinfos)
                    print(f"DEBUG: jobinfo count = {job_count}")

                if segment_group == OTHER and check_income_gel > 0 and job_count < 1:
                    print("DEBUG: Approve path (segment_group=OTHER, income>0, job_count<1)")
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "A400", "Low Risk", result="Approve")

            elif segment_group == PHOTOS:
                print("DEBUG: segment_group == PHOTOS")
                if bureau_grade in ["A", "B", "C1", "C2", "C3", "D1"]:
                    print("DEBUG: bureau_grade is low risk → Approve")
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "A400", "Low Risk", result="Approve")
                else:
                    print("DEBUG: bureau_grade not low risk → Decline")
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_FALSE
                    add_decision_once(record, "D124", "High Risk", result="Decline")
            else:
                print("DEBUG: Other segment_group → Default Approve")
                record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                add_decision_once(record, "A400", "Low Risk", result="Approve")

    # ========== STEP 2c ==========
    print(f"DEBUG: Checking STEP 2c conditions for applicant {i} ...")
    if (
        bureau_grade == "E2"
        and scoring_bin == 4
        and segment_group not in [PAYROLL_5, PAYROLL_3, PAYROLL_1, RS]
        and record.system.application.tbcbank.request.applicationdata.isselfemployedincomeflag
        == GDS_FALSE
    ):
        print("DEBUG: STEP 2c triggered (E2 + scoring_bin=4 + not payroll + selfemployed=FALSE)")

        if ism3_binclient == GDS_FALSE:
            print("DEBUG: ism3_binclient = FALSE → Decline case")
            add_decision_once(record, "D124", "High Risk", result="Decline")
            record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_FALSE
            continue

        if ism3_binclient == GDS_TRUE:
            print("DEBUG: ism3_binclient = TRUE → product_code & segment_group evaluation")
            if product_code != "CL_WS":
                print("DEBUG: product_code != CL_WS")
                if segment_group == OTHER:
                    print("DEBUG: segment_group == OTHER → Investigate")
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "I300", "Medium Risk", result="Investigate")

            if product_code == "CL_WS":
                print("DEBUG: product_code == CL_WS → checking job info")
                check_income_gel = app.jobs.checkincomegel
                print(f"DEBUG: check_income_gel = {check_income_gel}")

                jobinfos = safe_get_node(app.jobs.jobinfo)
                print(f"DEBUG: jobinfos = {jobinfos}")

                if jobinfos is None or jobinfos == []:
                    job_count = 0
                    print("DEBUG: No jobinfo found → job_count = 0")
                else:
                    job_count = len(jobinfos)
                    print(f"DEBUG: jobinfo count = {job_count}")

                if segment_group == OTHER and check_income_gel > 0 and job_count < 1:
                    print("DEBUG: Approve path (segment_group=OTHER, income>0, job_count<1)")
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "A400", "Low Risk", result="Approve")

            elif segment_group == PHOTOS:
                print("DEBUG: segment_group == PHOTOS")
                if bureau_grade in ["A", "B", "C1", "C2", "C3", "D1"]:
                    print("DEBUG: bureau_grade is low risk → Approve")
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "A400", "Low Risk", result="Approve")
                else:
                    print("DEBUG: bureau_grade not low risk → Decline")
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_FALSE
                    add_decision_once(record, "D124", "High Risk", result="Decline")
            else:
                print("DEBUG: Default Approve path in STEP 2c")
                record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                add_decision_once(record, "A400", "Low Risk", result="Approve")

print("\n=== DEBUG: Finished M3_BIN decision flow ===")
