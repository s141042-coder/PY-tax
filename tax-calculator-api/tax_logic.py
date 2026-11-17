"""
綜所稅計算核心模組 (以萬元為單位運算)
"""
from typing import Dict, Any, Tuple

# 課稅級距表 [級距下限, 稅率%, 累進差額]
TAX_BRACKETS = [
    [4400, 40, 955],
    [2350, 30, 340],
    [1170, 20, 104],
    [520, 12, 26],
    [0, 5, 0]
]

def calculate_tax(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    根據傳入的 JSON 結構計算綜合所得稅
    """
    age = payload.get("age", 0)
    has_spouse = payload.get("has_spouse", False)
    spouse_age = payload.get("spouse_age", 0)
    kids_quantity = payload.get("kids_quantity", 0)
    monthly_salary = payload.get("monthly_salary", 0) # 月薪 (元)
    
    # 扣除額相關欄位
    deduction_method = payload.get("deduction_method", "標準扣除額") # "標準扣除額" 或 "列舉扣除額"
    donate_general = payload.get("donate_general", 0) # 一般捐贈
    donate_gov = payload.get("donate_gov", 0) # 對政府捐贈
    insurance_general = payload.get("insurance_general", 0) # 一般人身保險
    insurance_social = payload.get("insurance_social", 0) # 勞健保
    medical_expenses = payload.get("medical_expenses", 0) # 醫藥費
    disaster_losses = payload.get("disaster_losses", 0) # 災害損失
    mortgage_interest = payload.get("mortgage_interest", 0) # 房貸利息
    
    # 特別扣除額相關欄位
    financial_trading_losses = payload.get("financial_trading_losses", 0)
    interest_income = payload.get("interest_income", 0) # 利息/股利 (千元)
    disabilities = payload.get("disabilities", 0) # 身障手冊數量
    undergrad_students = payload.get("undergrad_students", 0) # 大專以上學生數
    under_grade1_kids = payload.get("under_grade1_kids", 0) # 幼兒數量
    long_term_care_count = payload.get("long_term_care_count", 0) # 長照人數
    has_house = payload.get("has_house", True)
    rent_paid = payload.get("rent_paid", 0) # 租金
    
    # 退休金相關
    has_retirement_income = payload.get("has_retirement_income", False)
    retirement_amount = payload.get("retirement_amount", 0)
    retirement_claim_type = payload.get("retirement_claim_type", "單次") # "單次" 或 "分期"

    # 1. 換算年薪與基礎所得額 (單位：萬)
    annual_salary_income = (monthly_salary * 12) / 10000.0
    individual_income = annual_salary_income
    gross_income_amount = annual_salary_income

    # 免稅額計算 (免稅額基礎 6 萬)
    if individual_income >= 60:
        individual_income -= 60
    else:
        individual_income = 0.0

    # 退休金處理
    if has_retirement_income:
        if retirement_claim_type == "單次":
            if retirement_amount >= 300:
                individual_income += 300
            elif retirement_amount >= 150:
                individual_income += (retirement_amount * 0.5)
        else:
            if retirement_amount >= 65:
                individual_income += (retirement_amount - 65)

    # 2. 免稅額調整 (所得稅法 17-1-1)
    if age >= 60 and not has_spouse:
        individual_income -= 30
    elif age >= 60 and has_spouse and spouse_age >= 60:
        individual_income -= 30

    if kids_quantity > 1:
        individual_income -= 30

    # 3. 扣除額計算 (所得稅法 17-1-2)
    if deduction_method == "標準扣除額":
        individual_income -= 120
    else:
        # 列舉扣除額
        max_donate = gross_income_amount * 0.2
        individual_income -= min(donate_general, max_donate)
        individual_income -= donate_gov
        individual_income -= min(insurance_general, 24)
        individual_income -= insurance_social
        individual_income -= medical_expenses
        individual_income -= disaster_losses
        individual_income -= min(mortgage_interest, 300)

    # 4. 特別扣除額 (所得稅法 17-1-2-3)
    individual_income -= financial_trading_losses

    # 薪資所得特別扣除額
    if annual_salary_income >= 200:
        individual_income -= 200
    else:
        individual_income -= annual_salary_income

    # 利息股利特別扣除額
    if interest_income > 0:
        taxable_interest = interest_income / 1000.0
        if taxable_interest >= 270:
            individual_income += (taxable_interest - 270)

    # 身心障礙與各項特別扣除額
    individual_income -= (200 * disabilities)
    individual_income -= (25 * undergrad_students)
    
    if under_grade1_kids == 1:
        individual_income -= 150
    elif under_grade1_kids > 1:
        individual_income -= (150 * under_grade1_kids)

    individual_income -= (180 * long_term_care_count)

    if not has_house:
        individual_income -= min(rent_paid, 200)

    # 應課稅所得金額不能為負數
    taxable_income = max(0.0, individual_income)

    # 5. 計算應納稅額
    tax_payable = 0.0
    applied_rate = 0
    progressive_difference = 0

    for bracket_limit, rate, diff in TAX_BRACKETS:
        if taxable_income > bracket_limit:
            applied_rate = rate
            progressive_difference = diff
            tax_payable = ((taxable_income - bracket_limit) * (rate / 100.0)) + diff
            break

    return {
        "gross_income_wan": round(gross_income_amount, 2),
        "taxable_income_wan": round(taxable_income, 2),
        "tax_rate_percent": applied_rate,
        "progressive_difference_wan": progressive_difference,
        "tax_payable_wan": round(tax_payable, 2),
        "tax_payable_twd": int(tax_payable * 10000)
    }
