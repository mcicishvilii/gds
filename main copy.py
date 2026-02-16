from datetime import timedelta

def uf_control_group_scoring_is_sec_loan_6_month(apm_applications, tbc_loans, application_date, is_self_employed_income_flag):

    if tbc_loans.GetNodeKey() != -1:
        for j in range(len(tbc_loans)):
            tbc_loan = tbc_loans[j]

            product_name = tbc_loan.productname
            is_in_control_group_flag = tbc_loan.isincontrolgroupflag
            customer_role = tbc_loan.customerrole
            start_date = tbc_loan.startdate

            app_date_less_than_6_months = (application_date - start_date) < timedelta(days=182)

            if (
                product_name == "FCL"
                and is_in_control_group_flag == GDS_TRUE
                and customer_role == CLIENT_ROLE_BORROWER
                and app_date_less_than_6_months
            ):
                return False

    if apm_applications.GetNodeKey() != -1:
        for j in range(len(apm_applications)):
            apm_application = apm_applications[j]

            product_name = apm_application.productname
            is_in_control_group_flag = apm_application.isincontrolgroupflag
            is_in_progress = apm_application.isinprogress
            decision_status = apm_application.applicationdecisionstatus

            if (
                product_name in ("CL_WS", "FCL")
                and is_in_control_group_flag == GDS_TRUE
                and is_in_progress == GDS_TRUE
                and decision_status == "APPROVE"
            ):
                return False

    if tbc_loans.GetNodeKey() != -1:
        for j in range(len(tbc_loans)):
            loan = tbc_loans[j]

            product_name = loan.productname
            start_date = loan.startdate
            max_dpd_6_months = loan.maxdpd6months or 0
            is_restructurized = loan.isrestructurized

            app_date_less_than_12 = (application_date - start_date) < timedelta(days=365)

            if (
                product_name in {"CONSUMER_LOAN","MORTGAGE_LOAN"}
                and app_date_less_than_12
                and max_dpd_6_months < 8
                and is_restructurized == GDS_FALSE
                and is_self_employed_income_flag == GDS_FALSE
            ):
                return True

    return False