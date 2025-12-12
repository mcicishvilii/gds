if (
    (account.cashwithdrawalfeerate == 0 or account.selectedtowithdraw == GDS_FALSE)
    and new_account_cash_withdrawal_branch is not None
    and new_account_cash_withdrawal_atm is not None
):
    cash_withdrawal_fee_rate = max(
        new_account_cash_withdrawal_branch, new_account_cash_withdrawal_atm
    )
