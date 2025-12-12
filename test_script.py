import math
import numpy_financial as npf

request = record.system.application.tbcbank.request
node_currency = request.applicationdata.currency
fx_rates = normalize(request.generalinfo.exchangerates.exchangerate)
NBGExchangeRates = fx_rates[fx_rates["ExchangeRateType"] == "NBG"]

# ==========================================
# 1. GLOBAL CONFIG & DATA STRUCTURES
# ==========================================

fixed_insurance = 0

EFF_APR_CONSTRAINTS = {
    (0, 299):     [35, 35, 35, 35, 45, 48, 48, 48],
    (300, 80000): [18, 18, 18, 18, 24, 30, 48, 48],
}

CONSTRAINT_BUCKETS = [14.9, 15.9, 18.9, 21.9, 24.9, 26.9, 28.9, 999.9]


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
    
    fee_amt = max(req_amount * disb_rate_param / 100 , disb_min_param)
    net_limit = req_amount - fee_amt
    client_pmt = available_pmt - fixed_insurance
    
    is_test_group = str(app_id).endswith("0")
    
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
        eff_apr_dec = final_eff_apr / 100.0
        new_net_limit = npf.pv(eff_apr_dec/12, final_term, -available_pmt)

        gross_via_pct = new_net_limit / (1 - disb_rate_param / 100)
        fee_via_pct = gross_via_pct * disb_rate_param / 100
        
        if fee_via_pct >= disb_min_param:
            final_limit = gross_via_pct
        else:
            final_limit = new_net_limit + disb_min_param
        
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
        "IsNPVInfinity": is_npv_infinity,
        "EffAPR": final_eff_apr,
        "DisbursementFeeRate": disb_rate_param
    }
    

# ==========================================
# 3.INPUTS
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

try:
    cb_fixed_fee_param = record.system.application.tbcbank.request.productpolicycatalogue.productpolicy.disbursementfeefixedamount
except:
    cb_fixed_fee_param = 0

try:
    payroll_cw_rate = record.system.application.tbcbank.request.offersdatacall.payrolloffer.cashwithdrawalfeerate
except:
    payroll_cw_rate = 0

try:
    acc_cw_rate = record.system.application.tbcbank.request.account.cashwithdrawalfeerate
except:
    acc_cw_rate = 0

try:
    acc_selected = record.system.application.tbcbank.request.account.selectedtowithdraw
except:
    acc_selected = GDS_FALSE

try:
    pol_atm_rate = record.system.application.tbcbank.request.productpolicycatalogue.productpolicy.newaccountcashwithdrawalfeerateatm
except:
    pol_atm_rate = None

try:
    pol_branch_rate = record.system.application.tbcbank.request.productpolicycatalogue.productpolicy.newaccountcashwithdrawalfeeratebranch
except:
    pol_branch_rate = None
    
try:
    sum_debt_payments = record.system.application.tbcbank.response.interimcalculations.interimcalculationsfornewlimit_checked.sumofcurrentdebtpayments or 0
except:
    sum_debt_payments = 0

try:
    sum_debt_payments_long = record.system.application.tbcbank.response.interimcalculations.interimcalculationsfornewlimit_checked.sumofcurrentdebtpayments_longterm or 0
except:
    sum_debt_payments_long = 0

try:
    check_income_gel = record.system.application.tbcbank.request.incomeestimations.applicationincomeestimation.incomeestimation.checkincomegel
    if check_income_gel is None: check_income_gel = 0
except:
    check_income_gel = 0

try:
    avail_payment_nbg = record.system.application.tbcbank.response.interimcalculations.interimcalculationsfornewlimit_checked.availablepaymentnbg or 0
except:
    avail_payment_nbg = 0

try:
    sum_debt_payments_nbg = record.system.application.tbcbank.response.interimcalculations.interimcalculationsfornewlimit_checked.sumofcurrentdebtpaymentsnbg or 0
except:
    sum_debt_payments_nbg = 0

spf_other_rate = 0
spf_tbc_rate = 0
spf_times_tbc_rate = 0
spf_times = 0

def get_fee_list(base_node):
    try:
        items = base_node.prepaymentfees.prepaymentfee
        if items is None: return []
        return items if isinstance(items, list) else [items]
    except:
        return []

policy_fee_list = get_fee_list(record.system.application.tbcbank.request.productpolicycatalogue.productpolicy)
payroll_fee_list = get_fee_list(record.system.application.tbcbank.request.offersdatacall.payrolloffer)

for i in range(len(policy_fee_list)):
    item = policy_fee_list[i]
    try:
        if item.source == "PREPAYMENTFEE_SOURCE_OTHER":
            spf_other_rate = item.rate
            break
    except: pass

target_list = payroll_fee_list if (is_payroll_flag is GDS_TRUE) else policy_fee_list

for i in range(len(target_list)):
    item = target_list[i]
    try:
        if item.source == "PREPAYMENTFEE_SOURCE_OWN":
            cnt = item.count or 0
            rt = item.rate or 0
            
            if cnt == 0:
                spf_tbc_rate = rt
            elif cnt > 0:
                spf_times_tbc_rate = rt
                spf_times = cnt
    except: pass


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
final_eff_apr = result['EffAPR']

final_term_for_long = record.system.application.tbcbank.response.loanparameters.maxloanterm

new_pmt_for_long = npf.pmt(rate=final_rate/12, nper=final_term_for_long, pv=-final_limit)
new_pmt_for_st = npf.pmt(rate=final_rate/12, nper=final_term, pv=-final_limit)

final_monthly_payment_amount = new_pmt_for_st + fixed_insurance
final_monthly_payment_amount_long = new_pmt_for_long + fixed_insurance

final_cb_fixed_fee = cb_fixed_fee_param

if is_payroll_flag is GDS_TRUE:
    final_disbursement_fee_value = final_limit * (disbursement_fee_rate / 100)
else:
    final_disbursement_fee_value = max(final_limit * (disbursement_fee_rate / 100), disbursement_fee_min_amount)


final_cash_withdrawal_fee_rate = 0
if is_payroll_flag is GDS_TRUE:
    final_cash_withdrawal_fee_rate = payroll_cw_rate
else:
    final_cash_withdrawal_fee_rate = acc_cw_rate
    condition_check = (acc_cw_rate == 0) or (acc_selected is GDS_FALSE)
    if condition_check and (pol_atm_rate is not None) and (pol_branch_rate is not None):
        final_cash_withdrawal_fee_rate = max(pol_atm_rate, pol_branch_rate)

current_disbursement_fee = max(final_limit * (disbursement_fee_rate / 100), disbursement_fee_min_amount)
final_cash_withdrawal_fee = (final_limit - current_disbursement_fee - final_cb_fixed_fee) * final_cash_withdrawal_fee_rate

rate_to_gel = uf_currency_conversion_logic(fx_rates, node_currency, "GEL", NBGExchangeRates)


final_net_amount = final_limit - final_disbursement_fee_value - final_cb_fixed_fee - final_cash_withdrawal_fee

final_monthly_payment_amount_gel = final_monthly_payment_amount * rate_to_gel
final_monthly_payment_amount_long_gel = final_monthly_payment_amount_long * rate_to_gel

final_total_repayment = final_monthly_payment_amount * final_term

final_rise_in_price = final_total_repayment - final_limit

if check_income_gel > 0:
    final_pti = (final_monthly_payment_amount + sum_debt_payments) / check_income_gel
    final_pti_long = (final_monthly_payment_amount_long + sum_debt_payments_long) / check_income_gel
else:
    final_pti = 0
    final_pti_long = 0
    
if final_monthly_payment_amount > avail_payment_nbg:
    final_pti_nbg = final_pti_long
else:
    if check_income_gel > 0:
        final_pti_nbg = (sum_debt_payments_nbg + final_monthly_payment_amount) / check_income_gel
    else:
        final_pti_nbg = 0


offerinfos = safe_get_node(record.system.application.tbcbank.response.offers.offerinfo)

if len(offerinfos) == 0:
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.termmonths = final_term
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.interestrate = final_rate
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.monthlypaymentamount = final_monthly_payment_amount
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.monthlypaymentamountgel = final_monthly_payment_amount_gel
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.longtermmonthlypaymentamount = final_monthly_payment_amount_long
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.longtermmonthlypaymentamountgel = final_monthly_payment_amount_long_gel
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.firsttrancheamountdisbursed = 0
    record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.secondtrancheamountdisbursed = 0
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.growthlimit = 0
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.netgrowthlimit = 0
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.effectiveapr = 20 # droebiti
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.disbursementfeerate = disbursement_fee_rate
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.disbursementfee = final_disbursement_fee_value
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.netamount = final_net_amount
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.totalrepayment = final_total_repayment
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.riseinprice = final_rise_in_price
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.pti = final_pti
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.pti_longterm = final_pti_long
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.pti_nbg = final_pti_nbg
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.spfotherbankrate = spf_other_rate
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.spftbcrate = spf_tbc_rate
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.spftimestbcrate = spf_times_tbc_rate
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.spftimes = spf_times
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.disbursementfeeminamount = disbursement_fee_min_amount
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.isnpvinfinity = final_is_infinity
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.cbfixedfeeamount = final_cb_fixed_fee
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.cashwithdrawalfeerate = final_cash_withdrawal_fee_rate
    record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.cashwithdrawalfee = final_cash_withdrawal_fee
    
    if str(applicationid).endswith("0"):
        record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.npveffectiveapr = final_eff_apr
    else:
        record.system.application.tbcbank.response.offers.offerinfo[0].offerdetails.npveffectiveapr = None
        
    if final_limit != credit_limit_amount:
        record.system.application.tbcbank.response.offers.offerinfo[0].creditproduct.creditlimitamount = final_limit

else:
    for i in range(len(offerinfos)):
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.termmonths = final_term
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.interestrate = final_rate
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.monthlypaymentamount = final_monthly_payment_amount
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.monthlypaymentamountgel = final_monthly_payment_amount_gel
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.longtermmonthlypaymentamount = final_monthly_payment_amount_long
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.longtermmonthlypaymentamountgel = final_monthly_payment_amount_long_gel
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.firsttrancheamountdisbursed = 0
        record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.secondtrancheamountdisbursed = 0
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.growthlimit = 0
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.netgrowthlimit = 0
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.effectiveapr = 20 # droebiti
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.isnpvinfinity = final_is_infinity
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.cbfixedfeeamount = final_cb_fixed_fee
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.cashwithdrawalfeerate = final_cash_withdrawal_fee_rate
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.cashwithdrawalfee = final_cash_withdrawal_fee
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.disbursementfeerate = disbursement_fee_rate
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.disbursementfee = final_disbursement_fee_value
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.netamount = final_net_amount
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.totalrepayment = final_total_repayment
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.riseinprice = final_rise_in_price
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.pti = final_pti
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.pti_longterm = final_pti_long
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.pti_nbg = final_pti_nbg
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.spfotherbankrate = spf_other_rate
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.spftbcrate = spf_tbc_rate
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.spftimestbcrate = spf_times_tbc_rate
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.spftimes = spf_times
        record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.disbursementfeeminamount = disbursement_fee_min_amount
        if str(applicationid).endswith("0"):
            record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.npveffectiveapr = final_eff_apr
        else:
            record.system.application.tbcbank.response.offers.offerinfo[i].offerdetails.npveffectiveapr = None
        if final_limit != credit_limit_amount:
            record.system.application.tbcbank.response.offers.offerinfo[i].creditproduct.creditlimitamount = final_limit
