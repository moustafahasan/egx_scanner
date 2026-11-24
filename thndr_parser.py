import re
import io
import pandas as pd
from pypdf import PdfReader

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

def _normalize_text(txt: str) -> str:
    txt = txt.translate(ARABIC_DIGITS)
    txt = txt.replace(",", "").replace("،", "")
    return txt

def _match_symbol_from_text(line_or_doc: str, known_names: dict) -> str:
    upper_txt = line_or_doc.upper()

    # 1) البحث المباشر عن كود السهم (مثل ABUK أو ABUK.CA أو EGX:ABUK)
    for sym in known_names.keys():
        if re.search(rf"(?<![A-Z0-9]){re.escape(sym)}(?:\.CA)?(?![A-Z0-9])", upper_txt):
            return sym

    # 2) المطابقة باسم الشركة العربي أو الإنجليزي داخل الفاتورة
    for sym, ar_name in known_names.items():
        clean_ar = re.sub(r"\(.*?\)", "", ar_name).strip()
        if len(clean_ar) >= 5 and clean_ar in line_or_doc:
            return sym

    # 3) استخراج أي رمز إنجليزي من 4 أحرف متبوع بـ .CA
    m_ca = re.search(r"\b([A-Z]{3,5})\.CA\b", upper_txt)
    if m_ca:
        return m_ca.group(1)

    return ""

def parse_thndr_files(uploaded_files, known_names: dict) -> list:
    """
    يقرأ ملفات فواتير وكشوف ثاندر (PDF / CSV / XLSX) ويعيد قائمة بالعمليات المستخرجة.
    """
    extracted_ops = []

    for up in uploaded_files:
        fname = up.name.lower()

        # أولاً: ملفات PDF (فواتير تنفيذ ثاندر أو كشف الحساب)
        if fname.endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(up.read()))
                full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
                norm_txt = _normalize_text(full_text)
                lines = [ln.strip() for ln in norm_txt.splitlines() if ln.strip()]

                # تحديد نوع العملية العام في الفاتورة
                doc_side = "شراء (Buy)"
                if re.search(r"\b(SELL|SALE)\b|بيع|أمر بيع|عملية بيع", norm_txt, re.IGNORECASE):
                    if not re.search(r"\b(BUY|PURCHASE)\b|شراء|أمر شراء", norm_txt, re.IGNORECASE):
                        doc_side = "بيع (Sell)"

                doc_sym = _match_symbol_from_text(norm_txt, known_names)

                # محاولة استخراج أسطر الجدول (رمز + كمية + سعر) لدعم الفواتير متعددة الأسهم
                found_in_lines = False
                for ln in lines:
                    ln_sym = _match_symbol_from_text(ln, known_names)
                    if not ln_sym:
                        continue
                    ln_side = doc_side
                    if re.search(r"\bSELL\b|بيع", ln, re.IGNORECASE):
                        ln_side = "بيع (Sell)"
                    elif re.search(r"\bBUY\b|شراء", ln, re.IGNORECASE):
                        ln_side = "شراء (Buy)"

                    nums = [float(x) for x in re.findall(r"\b\d+(?:\.\d+)?\b", ln)]
                    # استبعاد الأرقام الضخمة جداً (أرقام الفواتير/التواريخ)
                    valid_nums = [n for n in nums if 0.05 <= n <= 5000000 and n not in [2024, 2025, 2026, 2027]]
                    if len(valid_nums) >= 2:
                        # عادة الكمية عدد صحيح والسعر عشري أو أصغر من الإجمالي
                        int_cands = [n for n in valid_nums if float(n).is_integer() and 1 <= n <= 1000000]
                        price_cands = [n for n in valid_nums if not float(n).is_integer() and 0.05 <= n <= 5000]
                        qty = int(int_cands[0]) if int_cands else int(valid_nums[0])
                        price = float(price_cands[0]) if price_cands else float(valid_nums[1])
                        if qty > 0 and price > 0:
                            extracted_ops.append({
                                "المصدر": up.name,
                                "العملية": ln_side,
                                "الرمز": ln_sym,
                                "اسم الشركة": known_names.get(ln_sym, ln_sym),
                                "الكمية": qty,
                                "السعر": round(price, 4),
                            })
                            found_in_lines = True

                # إذا كانت الفاتورة لصفقة واحدة بصيغة مفتاح وقيمة (Key: Value)
                if not found_in_lines and doc_sym:
                    m_qty = re.search(r"(?:Quantity|Qty|Shares|الكمية|عدد الأسهم)\s*[:\-]?\s*(\d+)", norm_txt, re.IGNORECASE)
                    m_prc = re.search(r"(?:Execution Price|Price|Avg Price|سعر التنفيذ|السعر)\s*[:\-]?\s*(\d+(?:\.\d+)?)", norm_txt, re.IGNORECASE)
                    qty = int(m_qty.group(1)) if m_qty else 0  # V11.5: مفيش كمية افتراضية — لازم تدخلها في الجدول
                    price = float(m_prc.group(1)) if m_prc else 0.0
                    if price > 0:
                        extracted_ops.append({
                            "المصدر": up.name,
                            "العملية": doc_side,
                            "الرمز": doc_sym,
                            "اسم الشركة": known_names.get(doc_sym, doc_sym),
                            "الكمية": qty,
                            "السعر": round(price, 4),
                        })
            except Exception:
                pass

        # ثانياً: ملفات Excel / CSV
        elif fname.endswith((".csv", ".xlsx", ".xls")):
            try:
                df_in = pd.read_csv(up) if fname.endswith(".csv") else pd.read_excel(up)
                for _, row in df_in.iterrows():
                    row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                    sym = _match_symbol_from_text(row_str, known_names)
                    if not sym:
                        continue
                    side = "بيع (Sell)" if re.search(r"\bSELL\b|بيع", row_str, re.IGNORECASE) else "شراء (Buy)"
                    qty, price = 0, 0.0
                    for col in df_in.columns:
                        cl = str(col).lower()
                        val = row[col]
                        if pd.isna(val):
                            continue
                        if any(k in cl for k in ["qty", "quantity", "shares", "كمية", "الكمية"]):
                            qty = int(float(str(val).replace(",", "")))
                        elif any(k in cl for k in ["price", "avg", "سعر", "السعر"]):
                            price = float(str(val).replace(",", ""))
                    if qty > 0 and price > 0:
                        extracted_ops.append({
                            "المصدر": up.name,
                            "العملية": side,
                            "الرمز": sym,
                            "اسم الشركة": known_names.get(sym, sym),
                            "الكمية": qty,
                            "السعر": round(price, 4),
                        })
            except Exception:
                pass

    return extracted_ops