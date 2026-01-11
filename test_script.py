from datetime import timedelta

def uf_is_sec_loan_6_month_control_group(record):
    request = record.system.application.tbcbank.request
    applicants = request.applicants.applicant

    application_date = record.system.application.applicationdate
    is_self_employed_income_flag = request.applicationdata.isselfemployedincomeflag

    for i in range(len(applicants)):
        applicant = applicants[i]

        loans = applicant.internaldatainfo.basiccredithistory.loan
        for j in range(len(loans)):
            loan = loans[j]

            product_name = loan.productname
            is_in_control_group_flag = loan.isincontrolgroupflag
            customer_role = loan.customerrole
            start_date = loan.startdate

            app_date_less_than_6_months = (application_date - start_date) < timedelta(days=182)

            if (
                product_name == FCL
                and is_in_control_group_flag == GDS_TRUE
                and customer_role == CLIENT_ROLE_BORROWER
                and app_date_less_than_6_months
            ):
                return False

        apm_apps = applicant.internaldatainfo.apmapplicationhistory.apmapplication
        for j in range(len(apm_apps)):
            apm = apm_apps[j]

            product_name = apm.productname
            is_in_control_group_flag = apm.isincontrolgroupflag
            is_in_progress = apm.isinprogress
            decision_status = apm.applicationdecisionstatus

            if (
                product_name in (CL_WS, FCL)
                and is_in_control_group_flag == GDS_TRUE
                and is_in_progress == GDS_TRUE
                and decision_status == "APPROVE"
            ):
                return False

    for i in range(len(applicants)):
        applicant = applicants[i]
        loans = applicant.internaldatainfo.basiccredithistory.loan

        for j in range(len(loans)):
            loan = loans[j]

            product_name = loan.productname
            start_date = loan.startdate
            max_dpd_6_months = loan.maxdpd6months
            is_restructurized = loan.isrestructurized

            app_date_less_than_12 = (application_date - start_date) < timedelta(days=365)

            if (
                product_name == CONSUMER_LOAN
                and app_date_less_than_12
                and max_dpd_6_months < 8
                and is_restructurized == GDS_FALSE
                and is_self_employed_income_flag == GDS_FALSE
            ):
                return True

    return False
