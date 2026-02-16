request = record.system.application.tbcbank.request
product = record.system.application.decisionresponse.product

decisions = product.decision

recalculatecall = record.system.application.recalculatecall or GDS_FALSE
updatepricingflag = record.system.application.updatepricingflag or GDS_FALSE
behavioural_bin = record.system.application.tbcbank.request.applicationdata.behaviouralbin
scoring_bin = record.system.application.tbcbank.request.applicationdata.scoringbin
is_selfemployed_income_flag = record.system.application.tbcbank.request.applicationdata.isselfemployedincomeflag or GDS_FALSE
segment_group = record.system.application.tbcbank.response.checkresult.segmentgroup
check_income_gel = record.system.application.tbcbank.response.checkresult.incomeestimations.applicationincomeestimation.incomeestimation.checkincomegel or 0
bureau_grade = record.system.application.tbcbank.request.applicants.applicant[0].creditbureauinfo.creditrating.bureaugrade
tbc_employee = record.system.application.tbcbank.request.applicants.applicant[0].internaldatainfo.clientstatusinfo.tbcemployee or GDS_FALSE
exception_flag = record.system.application.tbcbank.request.applicants.applicant[0].internaldatainfo.clientstatusinfo.exceptionflag or GDS_FALSE

def decision_dependon_exceptionflag():
    if exception_flag == GDS_TRUE and segment_group != PHOTOS:
        add_decision_once(product, "D124", "High Risk", result="Investigate")
    else:
        add_decision_once(product, "D124", "High Risk", result="Decline")

def segment_group_common_decisions():
    if segment_group == OTHER or segment_group == PHOTOS:
        if segment_group == PHOTOS:
            if bureau_grade in ("A", "B", "C1", "C2", "C3", "D1"):
                add_decision_once(product, "A400", "Low Risk", result="Approve")
            else:
                decision_dependon_exceptionflag()
        else:
            if not check_income_gel:
                add_decision_once(product, "I300", "Medium Risk", result="Investigate")
            else:
                add_decision_once(product, "A400", "Low Risk", result="Approve")
    else:
        add_decision_once(product, "A400", "Low Risk", result="Approve")

#final decisions >
if tbc_employee == GDS_FALSE and recalculatecall == GDS_FALSE and updatepricingflag == GDS_FALSE:
    if behavioural_bin:
        if behavioural_bin > 6:
            decision_dependon_exceptionflag()
        else:
            if is_selfemployed_income_flag == GDS_TRUE:
                if behavioural_bin > 4:
                    decision_dependon_exceptionflag()
                else:
                    add_decision_once(product, "A400", "Low Risk", result="Approve")
            else:
                segment_group_common_decisions()
    else:
        if scoring_bin > 8:
            decision_dependon_exceptionflag()
        else:
            if is_selfemployed_income_flag == GDS_TRUE:
                if scoring_bin == 8:
                    decision_dependon_exceptionflag()
                else:
                    add_decision_once(product, "A400", "Low Risk", result="Approve")
            else:
                segment_group_common_decisions()
else:
    add_decision_once(product, "A400", "Low Risk", result="Approve")

application_date = record.system.application.applicationdate
is_self_employed_income_flag = record.system.application.tbcbank.request.applicationdata.isselfemployedincomeflag
applicants = record.system.application.tbcbank.request.applicants.applicant



for a in range(len(applicants)):
    applicant = applicants[a]
    apm_applications = applicant.internaldatainfo.apmapplicationhistory.apmapplication
    tbc_loans = applicant.internaldatainfo.basiccredithistory.loan
    
    exception_flag = applicant.internaldatainfo.clientstatusinfo.exceptionflag
    
    if uf_control_group_scoring_is_sec_loan_6_month(apm_applications, tbc_loans, application_date, is_self_employed_income_flag):
        if decisions.GetNodeKey() != -1 and len(decisions) != 0:
            for i in decisions.Indexes():
                code = decisions[i].reason.reasoncode
                if code == "D124" and exception_flag != GDS_TRUE:
                    decisions[i].Delete()
                    add_decision_once(product, "A400", "Low Risk", result="Approve")
                    request.applicationdata.isincontrolgroup = GDS_TRUE
                    request.applicationdata.controlgroup = "SecLoan6Month"
