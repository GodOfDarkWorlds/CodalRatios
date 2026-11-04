import csv
from os import system, environ
from json import loads
from time import sleep
from requests import get, Response
from requests.exceptions import ConnectionError as CE
from random import randint
from bs4 import BeautifulSoup
from urllib.parse import unquote
from fake_useragent import UserAgent
from re import compile, search, DOTALL




def show_banner() -> None:
    def link(url: str, text: str = None) -> str:
        text = text or url
        if not environ.get("WT_SESSION"):
            return text
        return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"

    system("")  # فعال کردن رنگ ANSI تو cmd ویندوز
    cyan, white, magenta = "\033[96m", "\033[97;1m", "\033[95m"
    red, dim, reset = "\033[91m", "\033[90m", "\033[0m"
    W = 50
    gh = "https://github.com/godOfDarkWorlds"

    def row(text="", color="", url=None):
        shown = link(url, text) if url else text
        pad = " " * (W - len(text))
        return f"{cyan}║{reset}{color}{shown}{reset}{pad}{cyan}║{reset}"

    print(cyan + "╔" + "═" * W + "╗" + reset)
    print(row())
    print(row("            C O D A L   R A T I O S", white))
    print(row("       Financial ratios from Codal reports", magenta))
    print(row())
    print(cyan + "╟" + "─" * W + "╢" + reset)
    print(row())
    print(row("   by A", dim))
    print(row("   " + "Github: " + gh, cyan, url=gh))
    print(row("   [!] For personal use only.", red))
    print(row())
    print(cyan + "╚" + "═" * W + "╝" + reset)
    print()


def request_to_sit(url: str, sheet_id: int) -> Response | int:
    split_url = url.split("?")
    letter_serial = unquote(split_url[1].split("&")[0].replace("LetterSerial=", "") if "&" in split_url[1] else
                            split_url[1].replace("LetterSerial=", ""))  # for making raw
    url = split_url[0]

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'User-Agent': UserAgent().random,
        'sec-ch-ua-platform': '"Windows"',
    }

    params = {
        "LetterSerial": letter_serial,
        "sheetId": sheet_id,  # need 0 , 1
    }

    response = get(url=url, headers=headers, params=params)

    if response.status_code == 200:
        return response

    return response.status_code


def retry_attempt(url: str, sheet_id: int) -> BeautifulSoup:
    how_many = 3

    for attempt in range(how_many):

        try:
            response = request_to_sit(url, sheet_id)

            if isinstance(response, int):
                if response == 404:
                    print("Can not Find Report.\nMake Sure Enter Valid Link.\n\n")
                    url_check(url=input("Enter Valid Link: "))
                    break

                print(f"HTTP Error: {response}\nReport To Creator.")

            return BeautifulSoup(response.text, 'html.parser')

        except CE:
            print("Connection Error!")

            if attempt + 1 == how_many:
                url_check(input("Can Not Reach The Site.\n\nTry Again Later Or Enter Url: "))
                break



            print(f"Retrying... Attempt {attempt + 2}")


def dict_extractor(url: str, sheet_id: int) -> dict | None:
    soup = retry_attempt(url, sheet_id)

    script_tag = soup.find("script", string=compile(r"var\s+datasource\s*="))
    company_name = str(soup.find("span", {"id": "ctl00_txbCompanyName"}).text)

    if script_tag:
        script_text = script_tag.string

    pattern = r"var\s+datasource\s*=\s*(\{.*?\});"
    data = loads(search(pattern, script_text, DOTALL).group(1))
    if data:
        data = data.get("sheets", None)
        if data:
            data = data[0].get("tables", None)
            if data:
                data = data[0].get("cells", None)
                if data:
                    return data, company_name
                else:
                    print("Cells not found")
            else:
                print("Table`s not found")
        else:
            print("Sheets not found")
    else:
        print("Data not found")
    url_check(input("Can Not Get Data.\n\nTry Again Later Or Enter Url: "))


def values_extractor(url: str, sheet_id: int = 0) -> tuple[dict[str, list[int]], str]:
    name_to_code = {"جمع دارايي\u200cهاي جاري": "A", "جمع بدهي\u200cهاي جاري": "B",
                    "سفارشات و پيش\u200cپرداخت\u200cها": "C", "موجودي مواد و کالا": "D",
                    "سرمايه\u200cگذاري\u200cهاي کوتاه\u200cمدت": "E", "موجودي نقد": "F", "درآمدهاي عملياتي": "G",
                    "دريافتني\u200cهاي تجاري و ساير دريافتني\u200cها": "H", "بهاى تمام شده درآمدهاي عملياتي": "I",
                    "سود(زيان) ناخالص": "J", "سود(زيان) عملياتى": "K", "سود(زيان) خالص": "L", "جمع حقوق مالکانه": "M",
                    "جمع دارايي\u200cها": "N", "جمع بدهي\u200cها": "P", "دارايي\u200cهاي ثابت مشهود": "Q",
                    "جمع بدهي\u200cهاي غيرجاري": "R", "هزينه\u200f هاى مالى": "S"}

    def _value(i):
        return int(i["value"].lstrip("-")) if i["value"].lstrip("-").isdigit() else i["value"]

    temp_dict = {}
    final_dict = {}

    while sheet_id <= 1:
        if sheet_id < 1:
            sleep(randint(2, 4))
        if sheet_id == 0:
            table_rows = ["1", "5", "14", "15", "16", "17", "18", "21", "22", "42", "35", "52", "53"]
        elif sheet_id == 1:
            table_rows = ["4", "5", "6", "11", "12", "21"]

        data, company_name = dict_extractor(url=url, sheet_id=sheet_id)
        for table_row in table_rows:
            o = None
            first = mid = last = None
            for i in data:
                v = i.values()
                if "A" + table_row in v and i["columnSequence"] == 1:
                    o = "date" if i["value"] == "شرح" else name_to_code[i["value"]]
                elif "B" + table_row in v and i["columnSequence"] == 2:
                    first = _value(i)
                elif "C" + table_row in v and i["columnSequence"] == 3:
                    mid = _value(i)
                elif "D" + table_row in v and i["columnSequence"] == 4:
                    last = _value(i)

                """
                # last column Persent
                # if "E" + table_row  in v and i["columnSequence"] == 5:
                #     temp_dict.append(i["value"])
                """

            temp_dict[o] = [
                first,
                mid,
                last
            ]

        final_dict.update(temp_dict)

        sheet_id += 1

    return final_dict, company_name


def safe_div(a, b):
    try:
        if b == 0:
            return "None"
        return a / b
    except (TypeError, ZeroDivisionError):
        return "None"

def safe_mul(a):
    if a == "None":
        return "None"
    return a * 100

def avg(a, b):
    try:
        return safe_div(a=(a + b) , b=2)
    except TypeError:
        return "None"

def calculator(url: str) -> tuple[dict[str, list[str]], str]:
    data, company_name = values_extractor(url=url)

    date = data.pop("date")
    current_ratio = []  # نسبت جاری
    quick_ratio = []  # نسبت آنی
    cash_ratio = []  # نسبت نقدی
    cash_to_current_liabilities = []  # نسبت وجه نقد به بدهی جاری
    ##################################
    inventory_turnover = []  # گردش موجودی مواد و کالا
    days_inventory_outstanding = []  # دوره نگهداری موجودی کالا
    receivables_turnover = []  # گردش حساب‌های دریافتنی
    days_sales_outstanding = []  # دوره وصول مطالبات
    total_asset_turnover = []  # گردش کل دارایی‌ها
    fixed_asset_turnover = []  # گردش دارایی‌های ثابت
    ##################################
    gross_profit_margin = []  # حاشیه سود ناخالص
    operating_profit_margin = []  # حاشیه سود عملیاتی
    net_profit_margin = []  # حاشیه سود خالص
    return_on_assets = []  # ROA بازده دارایی‌ها
    return_on_equity = []  # ROE بازده حقوق مالکانه
    ##################################
    debt_ratio = []  # نسبت بدهی
    debt_to_equity_ratio = []  # نسبت بدهی به حقوق مالکانه
    equity_ratio = []  # نسبت مالکانه
    long_term_debt_to_equity = []  # نسبت بدهی بلندمدت به حقوق مالکانه
    interest_coverage_ratio = []  # نسبت پوشش هزینه مالی
    for i in range(3):
        current_ratio.append(safe_div(data["A"][i], data["B"][i]))
        quick_ratio.append(safe_div((data["A"][i] - data["D"][i] - data["C"][i]), data["B"][i]))
        cash_ratio.append(safe_div((data["F"][i] + data["E"][i]), data["B"][i]))
        cash_to_current_liabilities.append(safe_div(data["F"][i], data["B"][i]))
        ##################################

        if i < 2:
            it = safe_div(a=data["I"][i], b=avg(a=data["D"][i] ,b=data["D"][i + 1]))
            rt = safe_div(a=data["G"][i], b=avg(a=data["H"][i] ,b=data["H"][i + 1]))

            inventory_turnover.append(it)
            days_inventory_outstanding.append(safe_div(184, it))

            receivables_turnover.append(rt)
            days_sales_outstanding.append(safe_div(184, rt))

            total_asset_turnover.append(safe_div(a=data["G"][i], b=avg(a=data["N"][i], b=data["N"][i + 1])))
            fixed_asset_turnover.append(safe_div(a=data["G"][i], b=avg(a=data["Q"][i], b=data["Q"][i + 1])))
            ##################################
            return_on_assets.append(
                safe_mul(safe_div(a=data["L"][i], b=avg(a=data["N"][i], b=data["N"][i + 1])))
            )

            return_on_equity.append(
                safe_mul(safe_div(a=data["L"][i], b=avg(a=data["M"][i], b=data["M"][i + 1])))
            )
        else:
            inventory_turnover.append("None")
            days_inventory_outstanding.append("None")
            receivables_turnover.append("None")
            days_sales_outstanding.append("None")
            total_asset_turnover.append("None")
            fixed_asset_turnover.append("None")
            ##################################
            return_on_assets.append("None")
            return_on_equity.append("None")

        ##################################
        gross_profit_margin.append(safe_mul(safe_div(data["J"][i], data["G"][i])))
        operating_profit_margin.append(safe_mul(safe_div(data["K"][i], data["G"][i])))
        net_profit_margin.append(safe_mul(safe_div(data["L"][i], data["G"][i])))
        ##################################
        debt_ratio.append(safe_mul(safe_div(data["P"][i], data["N"][i])))
        debt_to_equity_ratio.append(safe_div(data["P"][i], data["M"][i]))
        equity_ratio.append(safe_mul(safe_div(data["M"][i], data["N"][i])))
        long_term_debt_to_equity.append(safe_div(data["R"][i], data["M"][i]))
        interest_coverage_ratio.append(safe_div(data["K"][i], data["S"][i]))

    # نسبت‌های درصدی
    percentage_ratios = [
        current_ratio,
        debt_ratio,
        equity_ratio,
        gross_profit_margin,
        operating_profit_margin,
        net_profit_margin,
        return_on_assets,
        return_on_equity
    ]

    # نسبت‌های عددی با دو رقم اعشار
    decimal_ratios = [
        quick_ratio,
        cash_ratio,
        cash_to_current_liabilities,
        inventory_turnover,
        receivables_turnover,
        total_asset_turnover,
        fixed_asset_turnover,
        debt_to_equity_ratio,
        long_term_debt_to_equity,
        interest_coverage_ratio
    ]

    # نسبت‌های روزانه
    day_ratios = [
        days_inventory_outstanding,
        days_sales_outstanding
    ]

    for ratios in percentage_ratios:
        for i, value in enumerate(ratios):
            if value is not None and value != "None":
                ratios[i] = f"{value:.2f}%"

    for ratios in decimal_ratios:
        for i, value in enumerate(ratios):
            if value is not None and value != "None":
                ratios[i] = round(value, 2)

    for ratios in day_ratios:
        for i, value in enumerate(ratios):
            if value is not None and value != "None":
                ratios[i] = f"{value:.2f} روز"

    final_dict = {
        "date": date,
        "current_ratio": current_ratio,
        "quick_ratio": quick_ratio,
        "cash_ratio": cash_ratio,
        "cash_to_current_liabilities": cash_to_current_liabilities,
        "inventory_turnover": inventory_turnover,
        "days_inventory_outstanding": days_inventory_outstanding,
        "receivables_turnover": receivables_turnover,
        "days_sales_outstanding": days_sales_outstanding,
        "total_asset_turnover": total_asset_turnover,
        "fixed_asset_turnover": fixed_asset_turnover,
        "gross_profit_margin": gross_profit_margin,
        "operating_profit_margin": operating_profit_margin,
        "net_profit_margin": net_profit_margin,
        "return_on_assets": return_on_assets,
        "return_on_equity": return_on_equity,
        "debt_ratio": debt_ratio,
        "debt_to_equity_ratio": debt_to_equity_ratio,
        "equity_ratio": equity_ratio,
        "long_term_debt_to_equity": long_term_debt_to_equity,
        "interest_coverage_ratio": interest_coverage_ratio,
    }
    return final_dict, company_name


def save_csv(data, filename="financial_ratios.csv") -> None:
    names = {
        "current_ratio": "نسبت جاری",
        "quick_ratio": "نسبت آنی",
        "cash_ratio": "نسبت وجه نقد",
        "cash_to_current_liabilities": "نسبت وجه نقد به بدهی‌های جاری",
        "inventory_turnover": "گردش موجودی کالا",
        "days_inventory_outstanding": "دوره نگهداری موجودی کالا",
        "receivables_turnover": "گردش حساب‌های دریافتنی",
        "days_sales_outstanding": "دوره وصول مطالبات",
        "total_asset_turnover": "گردش دارایی‌ها",
        "fixed_asset_turnover": "گردش دارایی‌های ثابت",
        "gross_profit_margin": "حاشیه سود ناخالص",
        "operating_profit_margin": "حاشیه سود عملیاتی",
        "net_profit_margin": "حاشیه سود خالص",
        "return_on_assets": "بازده دارایی‌ها (ROA)",
        "return_on_equity": "بازده حقوق مالکانه (ROE)",
        "debt_ratio": "نسبت بدهی",
        "debt_to_equity_ratio": "نسبت بدهی به حقوق مالکانه",
        "equity_ratio": "نسبت حقوق مالکانه",
        "long_term_debt_to_equity": "نسبت بدهی بلندمدت به حقوق مالکانه",
        "interest_coverage_ratio": "نسبت پوشش هزینه‌های مالی"
    }

    dates = [
        search(r"\d{4}/\d{2}/\d{2}", date).group()
        for date in data["date"]
    ]

    with open(filename, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)

        # سطر اول: نام ستون‌ها و تاریخ‌ها
        writer.writerow(["نام شاخص"] + dates)

        # سایر سطرها: نام فارسی شاخص و مقادیر
        for key, persian_name in names.items():
            values = data.get(key, [])

            values = [
                "" if value is None or value == "None" else value
                for value in values
            ]

            writer.writerow([persian_name] + values)


def main(url: str) -> None:
    print("Start Extracting Data...")
    data, company_name = calculator(url=url)
    save_csv(data=data, filename=f"{company_name}.csv")
    print("File Successfully Saved!")


def url_check(url: str) -> None:
    url = url
    codal_url = "https://codal.ir/Reports/"
    while True:
        if codal_url in url and "LetterSerial=" in url:
            main(url=url)
            break
        else:
            url = input("Please Enter Valid Codal Link: ")


if __name__ == "__main__":
    show_banner()
    try:
        url_check(input("Please Enter \"Codal\" Link: "))
    except Exception as e:
        print(f"Error: {e}")
    input("\nPress Enter to exit...")
