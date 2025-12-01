import math
import numpy_financial as npf

# ==========================================
# 1. GLOBAL CONFIG & DATA STRUCTURES
# ==========================================

fixed_insurance = 0

EFF_APR_CONSTRAINTS = {
    (0, 299):     [35, 35, 35, 35, 45, 48, 48, 48],
    (300, 80000): [18, 18, 18, 18, 24, 30, 48, 48],
}

CONSTRAINT_BUCKETS = [14.9, 15.9, 18.9, 21.9, 24.9, 26.9, 28.9, 999.9]

def lookup_eff_apr(bin_val, term, amount):
    for row in NPV_RATES:
        if row.bin == bin_val:
            if row.limit[0] <= amount < row.limit[1]:
                if row.term[0] <= term < row.term[1]:
                    return row.effapr
    return None

def get_constraint_max_term(amount, eff_apr_percent):
    selected_row = None
    
    if 0 <= amount <= 299:
        selected_row = EFF_APR_CONSTRAINTS.get((0, 299))
    elif amount >= 300:
        selected_row = EFF_APR_CONSTRAINTS.get((300, 80000))
    
    if not selected_row:
        return 48

    col_idx = 7
    for i, threshold in enumerate(CONSTRAINT_BUCKETS):
        if eff_apr_percent <= threshold:
            col_idx = i
            break
    
    val = selected_row[col_idx]
    return val

def get_fixed_insurance(amount):
    val = 0
    if amount <= 1000: val = 1
    elif amount <= 5000: val = 5
    elif amount <= 10000: val = 10
    elif amount <= 20000: val = 12
    elif amount <= 30000: val = 14
    elif amount <= 80001: val = 16
    
    return val

def calculate_offer(app_id, pricing_bin, req_amount, available_pmt, is_payroll, disb_rate_param, disb_min_param, product_min_term, product_max_term):
    
    fixed_insurance = get_fixed_insurance(req_amount)
    
    fee_amt = max(req_amount * disb_rate_param /100 , disb_min_param)
    net_limit = req_amount - fee_amt
    client_pmt = available_pmt - fixed_insurance
    
    is_test_group = str(app_id).endswith("0")
    
    # --- STEP 1: Iterative Term Calculation ---
    term_step1 = 0
    final_eff_apr = 0
    is_npv_infinity = False
    
    current_term_assumption = 12 
    history = []
    
    for iteration in range(1, 5):
        current_apr_val = lookup_eff_apr(pricing_bin, current_term_assumption, req_amount)
        if current_apr_val is None:
            break
            
        current_apr_decimal = current_apr_val / 100.0

        raw_nper = npf.nper(current_apr_decimal/12, available_pmt, -net_limit)
        calc_term = math.ceil(raw_nper)

        bucket_consistent = False
        if current_term_assumption < 37 and calc_term < 37:
            bucket_consistent = True
        elif current_term_assumption >= 37 and calc_term >= 37:
            bucket_consistent = True
            
        if bucket_consistent:
            term_step1 = calc_term
            final_eff_apr = current_apr_val
            break
        else:
            current_term_assumption = calc_term 
            
            if calc_term in history:
                is_npv_infinity = True
                term_step1 = calc_term
                final_eff_apr = current_apr_val
                break
            history.append(calc_term)
            
    if term_step1 == 0:
        term_step1 = 48 
        final_eff_apr = 26.0


    constraint_term = get_constraint_max_term(req_amount, final_eff_apr)
    term_step2 = max(term_step1, constraint_term)
    term_step3 = max(term_step2, product_min_term)    
    term_step4 = min(term_step3, product_max_term)

    final_limit = req_amount
    final_term = term_step4
    final_rate = 0
    
    if term_step1 == term_step4:
        final_term = term_step1
        try:
            final_rate = npf.rate(final_term, client_pmt, -net_limit, 0) * 12
        except Exception as e:
            final_rate = 0
    else:
        new_net_limit = req_amount - fee_amt

        gross_via_pct = new_net_limit / (1 - disb_rate_param / 100)
        fee_via_pct = gross_via_pct * disb_rate_param / 100
        
        if fee_via_pct >= disb_min_param:
            final_limit = gross_via_pct
        else:
            final_limit = new_net_limit + (disb_min_param / 100)
        final_fee = max(final_limit * disb_rate_param / 100, disb_min_param)
        final_net = final_limit - final_fee
        
        try:
            final_rate = npf.rate(final_term, client_pmt, -final_net, 0) * 12
        except Exception as e:
            final_rate = 0

    return {
        "Term": final_term,
        "Limit": final_limit,
        "InterestRate": final_rate,
        "IsNPVInfinity": is_npv_infinity
    }

# ==========================================
# 3. DATAVIEW360 INPUT RETRIEVAL
# ==========================================

try:
    applicationid = record.system.application.tbcbank.request.applicationdata.systeminformation.applicationid
except:
    applicationid = "1"

try:
    product_name = record.system.application.creditrequest.productcode
except:
    product_name = ""

try:
    min_loan_amt = record.system.application.tbcbank.request.productpolicycatalogue.productpolicy.minloanamount
    credit_limit_amount = min_loan_amt
except:
    credit_limit_amount = 0

try:
    avail_payment = record.system.application.tbcbank.response.interimcalculations.interimcalculationsfornewlimit_checked.availablepayment
    avail_payment_long = record.system.application.tbcbank.response.interimcalculations.interimcalculationsfornewlimit_checked.availablepaymentlongterm
    
    if avail_payment is None or avail_payment_long is None:
        pmt = 0
    else:
        pmt = min(avail_payment, avail_payment_long)
        if pmt == 0: pmt = 0
except:
    pmt = 0

try:
    pricingbin = record.system.application.tbcbank.request.applicationdata.pricingbin
except:
    pricingbin = 0

try:
    is_payroll_flag = record.system.application.tbcbank.request.applicationdata.ispayrollflag
except:
    is_payroll_flag = GDS_FALSE

if is_payroll_flag is GDS_TRUE:
    try:
        disb_rate_raw = record.system.application.tbcbank.request.offersdatacall.payrolloffer.disbursementfeerate or 0
    except:
        disb_rate_raw = 0
else:
    try:
        disb_rate_raw = record.system.application.tbcbank.request.productpolicycatalogue.productpolicy.disbursementfeerate or 0
    except:
        disb_rate_raw = 0

disbursement_fee_rate = disb_rate_raw

try:
    disbursement_fee_min_amount = record.system.application.tbcbank.request.productpolicycatalogue.productpolicy.disbursementfeeminamount or 0
except:
    disbursement_fee_min_amount = 0

try:
    min_loan_term = record.system.application.tbcbank.request.productpolicycatalogue.productpolicy.minloanterm or 6
except:
    min_loan_term = 6

try:
    max_loan_term = record.system.application.tbcbank.request.productpolicycatalogue.productpolicy.maxloanterm or 48
except:
    max_loan_term = 48

# ==========================================
# 4. EXECUTE ENGINE
# ==========================================

result = calculate_offer(
    app_id=applicationid,
    pricing_bin=pricingbin,
    req_amount=credit_limit_amount,
    available_pmt=pmt,
    is_payroll=(is_payroll_flag is GDS_TRUE),
    disb_rate_param=disbursement_fee_rate,
    disb_min_param=disbursement_fee_min_amount,
    product_min_term=min_loan_term,
    product_max_term=max_loan_term
)

# ==========================================
# 5. WRITE OUTPUTS
# ==========================================

final_term = result['Term']
final_limit = result['Limit']
final_rate = result['InterestRate']
final_is_infinity = GDS_TRUE if result['IsNPVInfinity'] else GDS_FALSE

new_pmt = npf.pmt(rate=final_rate/12, nper=final_term, pv=-final_limit)

offerinfos = safe_get_node(record.system.application.tbcbank.response.offers.offerinfo)

if len(offerinfos) == 0:
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.termmonths = final_term
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.interestrate = final_rate
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.monthlypaymentamount = new_pmt + fixed_insurance
    if final_limit != credit_limit_amount:
        record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.creditlimitamount = final_limit
    
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.isnpvinfinity = final_is_infinity
else:
    for i in range(len(offerinfos)):
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.termmonths = final_term
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.interestrate = final_rate
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.monthlypaymentamount = new_pmt + fixed_insurance
        if final_limit != credit_limit_amount:
            record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.creditlimitamount = final_limit
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.isnpvinfinity = final_is_infinity