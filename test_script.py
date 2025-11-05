scoring_bin = record.system.application.tbcbank.request.applicationdata.scoringbin
ism3_binclient = record.system.application.tbcbank.request.applicationdata.ism3_binclient
segment_group = record.system.application.tbcbank.response.checkresult.segmentgroup
apps = safe_get_node(record.system.application.tbcbank.request.applicants.applicant)
decisions = safe_get_node(record.system.application.decisionresponse.product.decision)

for r in range(len(decisions)):
    decision = decisions[r]
    _ = decision.decisionresult

for i in range(len(apps)):
    app = apps[i]

    try:
        bureau_grade = app.creditbureauinfo.creditrating.bureaugrade
    except Exception as e:
        bureau_grade = None

    # ========== STEP 2a ==========
    if (
        bureau_grade == "E3"
        and scoring_bin in [4, 5, 6, 7, 8]
        and ism3_binclient == GDS_FALSE
    ):
        add_decision_once(record, "D124", "High Risk", result="Decline")
        record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_FALSE
        continue

    # ========== STEP 2b ==========
    if bureau_grade == "E2" and scoring_bin in [5, 6, 7, 8]:

        if ism3_binclient == GDS_FALSE:
            add_decision_once(record, "D124", "High Risk", result="Decline")
            record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_FALSE
            continue

        if ism3_binclient == GDS_TRUE:
            if product_code != "CL_WS":
                if segment_group == OTHER:
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "I300", "Medium Risk", result="Investigate")

            if product_code == "CL_WS":
                check_income_gel = app.jobs.checkincomegel

                job_count = 0
                jobinfos = safe_get_node(app.jobs.jobinfo)

                if jobinfos is None or jobinfos == []:
                    job_count = 0
                else:
                    job_count = len(jobinfos)

                if segment_group == OTHER and check_income_gel > 0 and job_count < 1:
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "A400", "Low Risk", result="Approve")

            elif segment_group == PHOTOS:
                if bureau_grade in ["A", "B", "C1", "C2", "C3", "D1"]:
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "A400", "Low Risk", result="Approve")
                else:
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_FALSE
                    add_decision_once(record, "D124", "High Risk", result="Decline")
            else:
                record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                add_decision_once(record, "A400", "Low Risk", result="Approve")

    # ========== STEP 2c ==========
    if (
        bureau_grade == "E2"
        and scoring_bin == 4
        and segment_group not in [PAYROLL_5, PAYROLL_3, PAYROLL_1, RS]
        and record.system.application.tbcbank.request.applicationdata.isselfemployedincomeflag
        == GDS_FALSE
    ):
        if ism3_binclient == GDS_FALSE:
            add_decision_once(record, "D124", "High Risk", result="Decline")
            record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_FALSE
            continue

        if ism3_binclient == GDS_TRUE:
            if product_code != "CL_WS":
                if segment_group == OTHER:
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "I300", "Medium Risk", result="Investigate")

            if product_code == "CL_WS":
                check_income_gel = app.jobs.checkincomegel

                jobinfos = safe_get_node(app.jobs.jobinfo)

                if jobinfos is None or jobinfos == []:
                    job_count = 0
                else:
                    job_count = len(jobinfos)

                if segment_group == OTHER and check_income_gel > 0 and job_count < 1:
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "A400", "Low Risk", result="Approve")

            elif segment_group == PHOTOS:
                if bureau_grade in ["A", "B", "C1", "C2", "C3", "D1"]:
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                    add_decision_once(record, "A400", "Low Risk", result="Approve")
                else:
                    record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_FALSE
                    add_decision_once(record, "D124", "High Risk", result="Decline")
            
            else:
                record.system.application.tbcbank.request.applicationdata.isapprovedm3_bin = GDS_TRUE
                add_decision_once(record, "A400", "Low Risk", result="Approve")