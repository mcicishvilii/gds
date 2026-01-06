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
