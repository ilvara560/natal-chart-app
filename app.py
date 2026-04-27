import os
import sys
import json
import urllib.request
import urllib.error
import re  
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

# ==========================================
# 1. API呼び出し関数（ストリーミング対応版に変更）
# ==========================================
def get_gemini_reading_stream(api_key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={api_key}"
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    
    with urllib.request.urlopen(req) as response:
        for line in response:
            line = line.decode('utf-8').strip()
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk_json = json.loads(data_str)
                    if "candidates" in chunk_json and len(chunk_json["candidates"]) > 0:
                        parts = chunk_json["candidates"][0].get("content", {}).get("parts", [])
                        if parts:
                            chunk_text = parts[0].get("text", "")
                            yield chunk_text.replace('*', '')
                except json.JSONDecodeError:
                    pass

# ==========================================
# ロジック・テキスト出力・PDF出力
# ==========================================
class NatalChart:
    def __init__(self, name: str, birthdate: str):
        self.raw_name = name
        self.name = name.replace(" ", "").lower()
        self.birthdate = birthdate
        self.results = {}
        self._calculate()

    def _get_name_number(self, char: str) -> int:
        mapping = {1: "ajs", 2: "bkt", 3: "clu", 4: "dmv", 5: "enw", 6: "fox", 7: "gpy", 8: "hqz", 9: "ir"}
        for num, chars in mapping.items():
            if char in chars: return num
        return 0

    def _reduce_to_single(self, num: int) -> int:
        while num >= 10:
            num = sum(int(digit) for digit in str(num))
        return num

    def _get_personal_year(self, target_year: int, b_month: int, b_day: int) -> int:
        y_num = self._reduce_to_single(sum(int(d) for d in str(target_year)))
        m_num = self._reduce_to_single(b_month)
        d_num = self._reduce_to_single(b_day)
        return self._reduce_to_single(y_num + m_num + d_num)

    def _calculate(self):
        b_year, b_month, b_day = int(self.birthdate[:4]), int(self.birthdate[4:6]), int(self.birthdate[6:8])
        
        # VBA Ver.6.r.0 '- 2026.04.26 (2)' ロジックに準拠
        y_raw = sum(int(d) for d in str(b_year))      # 年の各桁の和
        m_raw = (b_month // 10) + (b_month % 10)      # 月の各桁の和
        d_raw = (b_day // 10) + (b_day % 10)          # 日の各桁の和

        # ★ Carmic Number の算出
        carmic1 = y_raw + m_raw + d_raw               # 全桁の単純合算
        
        def vba_reduce_once(n):
            return (n // 10) + (n % 10)
        carmic2 = vba_reduce_once(y_raw) + vba_reduce_once(m_raw) + vba_reduce_once(d_raw)
        
        a0 = b_year + b_month + b_day
        carmic3 = sum(int(d) for d in str(a0))
        
        carmic_0 = 0
        for c in (carmic1, carmic2, carmic3):
            if c in (13, 14, 16, 19):
                carmic_0 = c
        carmic_str = str(carmic_0) if carmic_0 != 0 else "-"

        # ★ Birth Number のマスターナンバー判定
        raw_birth = y_raw + m_raw + d_raw
        display_birth_num = self._reduce_to_single(raw_birth)
        temp_val = raw_birth
        while temp_val >= 10:
            if temp_val in (11, 22):
                display_birth_num = temp_val
                break
            temp_val = sum(int(digit) for digit in str(temp_val))

        # 以降の計算用（1桁還元）
        y_num = self._reduce_to_single(y_raw)
        m_num = self._reduce_to_single(b_month)
        d_num = self._reduce_to_single(b_day)
        birth_num = self._reduce_to_single(raw_birth)

        destiny_num = self._reduce_to_single(sum(self._get_name_number(c) for c in self.name))
        vowels = "aiueo"
        soul_num = self._reduce_to_single(sum(self._get_name_number(c) for c in self.name if c in vowels))
        perso_num = self._reduce_to_single(sum(self._get_name_number(c) for c in self.name if c not in vowels))
        realiz_num = self._reduce_to_single(birth_num + destiny_num)

        md_num = self._reduce_to_single(m_num + d_num)
        stage_num = self._reduce_to_single(y_num + m_num + d_num + md_num + birth_num + destiny_num + soul_num + perso_num + realiz_num)
        chall_num = self._reduce_to_single(birth_num + y_num + m_num + d_num + md_num)
        strengths = self._reduce_to_single(birth_num + chall_num)
        sub_theme = self._reduce_to_single(m_num + d_num)

        tp1, tp2, tp3 = 37 - birth_num, 50 - birth_num, 64 - birth_num
        s1_e = 36 - birth_num
        s2_e, s3_e = s1_e + 9, s1_e + 18

        pin = [self._reduce_to_single(m_num+d_num), self._reduce_to_single(d_num+y_num), self._reduce_to_single(self._reduce_to_single(m_num+d_num)+self._reduce_to_single(d_num+y_num)), self._reduce_to_single(m_num+y_num)]
        roots = [m_num, d_num, d_num, y_num]
        hards = [self._reduce_to_single(abs(m_num-d_num)), self._reduce_to_single(abs(d_num-y_num)), self._reduce_to_single(abs(self._reduce_to_single(abs(m_num-d_num))-self._reduce_to_single(abs(d_num-y_num)))), self._reduce_to_single(abs(m_num-y_num))]

        counts = {i: 0 for i in range(1, 10)}
        for c in self.name:
            n = self._get_name_number(c)
            if n > 0: counts[n] += 1

        magic_array = [
            0 if 0 in (counts[3], counts[6], counts[9]) else counts[3] + counts[6] + counts[9],
            0 if 0 in (counts[2], counts[5], counts[8]) else counts[2] + counts[5] + counts[8],
            0 if 0 in (counts[1], counts[4], counts[7]) else counts[1] + counts[4] + counts[7],
            0 if 0 in (counts[1], counts[2], counts[3]) else counts[1] + counts[2] + counts[3],
            0 if 0 in (counts[4], counts[5], counts[6]) else counts[4] + counts[5] + counts[6],
            0 if 0 in (counts[7], counts[8], counts[9]) else counts[7] + counts[8] + counts[9],
            0 if 0 in (counts[3], counts[5], counts[7]) else counts[3] + counts[5] + counts[7],
            0 if 0 in (counts[1], counts[5], counts[9]) else counts[1] + counts[5] + counts[9]
        ]
        max_nine = max(magic_array)
        nine_box_sums = [str(v) if v == max_nine else "_" for v in magic_array]
        
        self.results = {
            "BirthYear": b_year, "BirthMonth": b_month, "BirthDay": b_day,
            "BirthNum": display_birth_num, "DestinyNum": destiny_num, "SoulNum": soul_num, "PersoNum": perso_num, "RealizNum": realiz_num,
            "StageNum": stage_num, "ChallNum": chall_num, "Strengths": strengths, "SubTheme": sub_theme,
            "CarmicNum": carmic_str,
            "TP": [tp1, tp2, tp3], "Counts": counts,
            "MagicArray": magic_array, "NineBoxSums": nine_box_sums, "NineBoxMax": max_nine,
            "Stages": [
                {"term": "1st Stage", "age": f"0 ~ {s1_e}", "pin": pin[0], "root": roots[0], "hard": hards[0]},
                {"term": "2nd Stage", "age": f"{s1_e+1} ~ {s2_e}", "pin": pin[1], "root": roots[1], "hard": hards[1]},
                {"term": "3rd Stage", "age": f"{s2_e+1} ~ {s3_e}", "pin": pin[2], "root": roots[2], "hard": hards[2]},
                {"term": "4th Stage", "age": f"{s3_e+1} ~   ", "pin": pin[3], "root": roots[3], "hard": hards[3]}
            ]
        }

    def generate_report_text(self) -> str:
        res, c = self.results, self.results["Counts"]
        nbs = res["NineBoxSums"]
        lines = ["=" * 75, " " * 24 + "NATAL CHART ANALYSIS REPORT", "=" * 75]
        lines.append(f" Name      : {self.raw_name.upper()}")
        lines.append(f" Birthdate : {res['BirthYear']}/{res['BirthMonth']:02}/{res['BirthDay']:02}")
        lines.append("-" * 75)
        lines.append(" [ Core Numbers & Themes ]")
        lines.append(f"  Birth Number       : {res['BirthNum']}")
        lines.append(f"  Destiny Number     : {res['DestinyNum']}")
        lines.append(f"  Soul Number        : {res['SoulNum']}")
        lines.append(f"  Personality Number : {res['PersoNum']}")
        lines.append(f"  Realization Number : {res['RealizNum']}")
        lines.append(f"  Stage Number       : {res['StageNum']}")
        lines.append(f"  Challenge Number   : {res['ChallNum']}")
        lines.append(f"  New Strength       : {res['Strengths']}")
        lines.append(f"  Hidden Theme       : {res['SubTheme']}")
        lines.append(f"  Carmic Number      : {res['CarmicNum']}")
        lines.append("-" * 75)
        lines.append(" [ Turning Point Ages ]")
        lines.append(f"  1st Turning Point : {res['TP'][0]}")
        lines.append(f"  2nd Turning Point : {res['TP'][1]}  <-- (Main Turning Point)")
        lines.append(f"  3rd Turning Point : {res['TP'][2]}")
        lines.append("-" * 75)
        lines.append(" [ Life Cycle / Stage Periods ]")
        lines.append("  Term        start Age ~ end age    Milestone   Rout   Hardships")
        lines.append("  " + "-" * 63)
        for row in res["Stages"]:
            lines.append(f"   {row['term']}    {row['age']:>12}          {row['pin']}          {row['root']}          {row['hard']}")
        lines.append("-" * 75)
        lines.append(" [ Nine Box ]")
        lines.append("  (Character Counts in Name)\n")
        lines.append("       [3] [6] [9]      Sum Lines:")
        lines.append(f"        {c[3]}   {c[6]}   {c[9]}       3-6-9 : {nbs[0]}")
        lines.append(f"       [2] [5] [8]      2-5-8 : {nbs[1]}")
        lines.append(f"        {c[1]}   {c[4]}   {c[7]}       1-4-7 : {nbs[2]}")
        lines.append(f"       [1] [4] [7]      1-2-3 : {nbs[3]}")
        lines.append(f"        {c[1]}   {c[4]}   {c[7]}       4-5-6 : {nbs[4]}")
        lines.append(f"                        7-8-9 : {nbs[5]}")
        lines.append(f"                        3-5-7 : {nbs[6]}")
        lines.append(f"                        1-5-9 : {nbs[7]}")
        lines.append("-" * 75)
        lines.append(" [ Cycle 1-9 Status ]")
        lines.append("  1: Beginning   2: Alignment   3: Creation   4: Stability   5: Movement")
        lines.append("  6: Love        7: Reflection    8: Enrichment  9: Completion")
        lines.append("-" * 75)
        
        cycle_keywords = {
            1: "Beginning", 2: "Alignment", 3: "Creation", 4: "Stability", 5: "Movement",
            6: "Love", 7: "Reflection", 8: "Enrichment", 9: "Completion"
        }
        
        lines.append(" [ Year Cycle Table ]")
        lines.append("  Age | Year | Cyc Theme    || Age | Year | Cyc Theme    || Age | Year | Cyc Theme")
        lines.append("  " + "-" * 81)
        for r in range(27):
            row_str = ""
            for c_idx in range(3):
                age = r + c_idx * 27
                y = res["BirthYear"] + age
                cyc = self._get_personal_year(y, res["BirthMonth"], res["BirthDay"])
                theme = cycle_keywords.get(cyc, "")
                row_str += f" {age:>2} | {y} | {cyc} {theme:<10}"
                if c_idx < 2:
                    row_str += " ||"
            lines.append(f"  {row_str}")
        lines.append("=" * 75)
        return "\n".join(lines)

    def export_graphical_pdf(self, filename="Graphical_Report.pdf", ai_text=None):
        if not HAS_FPDF: return None
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_text_color(74, 144, 226)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "NATAL CHART ANALYSIS REPORT", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font("Helvetica", "", 10)
        b_date_str = f"{self.results['BirthYear']}{self.results['BirthMonth']:02}{self.results['BirthDay']:02}"
        pdf.cell(0, 10, f"Name: {self.raw_name.upper()}  |  Birthdate: {b_date_str}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)

        pdf.set_fill_color(245, 247, 250)
        pdf.set_text_color(74, 144, 226)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, " [ Core Numbers & Themes ]", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        res = self.results
        
        data_left = [["Birth Number", res["BirthNum"]], ["Destiny Number", res["DestinyNum"]], ["Soul Number", res["SoulNum"]], ["Personality Number", res["PersoNum"]], ["Realization Number", res["RealizNum"]]]
        data_right = [["Stage Number", res["StageNum"]], ["Challenge Number", res["ChallNum"]], ["New Strength", res["Strengths"]], ["Hidden Theme", res["SubTheme"]], ["Carmic Number", res["CarmicNum"]]]
        
        y_start = pdf.get_y()
        for item in data_left:
            pdf.cell(50, 7, item[0], border=1, new_x="RIGHT", new_y="TOP")
            pdf.cell(15, 7, str(item[1]), border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_xy(10 + 65 + 10, y_start)
        for item in data_right:
            pdf.set_x(10 + 65 + 10)
            pdf.cell(50, 7, item[0], border=1, new_x="RIGHT", new_y="TOP")
            pdf.cell(15, 7, str(item[1]), border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_y(y_start + (7 * 5) + 5)

        pdf.set_fill_color(245, 247, 250)
        pdf.set_text_color(74, 144, 226)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, " [ Turning Point Ages ]", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)

        y_start_tp = pdf.get_y()
        
        pdf.cell(35, 7, "1st Turning Point", border=1, new_x="RIGHT", new_y="TOP")
        pdf.cell(15, 7, f"{res['TP'][0]} yrs", border=1, new_x="RIGHT", new_y="TOP", align="C")
        
        pdf.set_xy(10 + 50 + 10, y_start_tp)
        pdf.cell(45, 7, "2nd Turning Point (Main)", border=1, new_x="RIGHT", new_y="TOP")
        pdf.cell(15, 7, f"{res['TP'][1]} yrs", border=1, new_x="RIGHT", new_y="TOP", align="C")
        
        pdf.set_xy(10 + 50 + 10 + 60 + 10, y_start_tp)
        pdf.cell(35, 7, "3rd Turning Point", border=1, new_x="RIGHT", new_y="TOP")
        pdf.cell(15, 7, f"{res['TP'][2]} yrs", border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.ln(5)

        pdf.set_fill_color(245, 247, 250)
        pdf.set_text_color(74, 144, 226)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f" [ Life Cycle Stages ]", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(30, 7, "Term", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(40, 7, "Age", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(30, 7, "Milestone", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(30, 7, "Rout", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(30, 7, "Hardships", border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "", 9)
        for s in res["Stages"]:
            pdf.cell(30, 7, s["term"], border=1, new_x="RIGHT", new_y="TOP")
            pdf.cell(40, 7, s["age"], border=1, new_x="RIGHT", new_y="TOP", align="C")
            pdf.cell(30, 7, str(s["pin"]), border=1, new_x="RIGHT", new_y="TOP", align="C")
            pdf.cell(30, 7, str(s["root"]), border=1, new_x="RIGHT", new_y="TOP", align="C")
            pdf.cell(30, 7, str(s["hard"]), border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.ln(5)
        
        pdf.set_fill_color(245, 247, 250)
        pdf.set_text_color(74, 144, 226)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, " [ Nine Box ]", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        c = res["Counts"]
        nbs = res["NineBoxSums"]
        y_start_nb = pdf.get_y()
        
        pdf.set_text_color(127, 140, 141)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(15, 6, "[3]", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, "[6]", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, "[9]", border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_text_color(74, 144, 226)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(15, 6, str(c[3]), border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, str(c[6]), border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, str(c[9]), border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_text_color(127, 140, 141)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(15, 6, "[2]", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, "[5]", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, "[8]", border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_text_color(74, 144, 226)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(15, 6, str(c[2]), border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, str(c[5]), border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, str(c[8]), border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_text_color(127, 140, 141)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(15, 6, "[1]", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, "[4]", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, "[7]", border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_text_color(74, 144, 226)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(15, 6, str(c[1]), border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, str(c[4]), border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(15, 6, str(c[7]), border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_text_color(0, 0, 0)

        pdf.set_xy(70, y_start_nb)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(30, 6, "Sum Lines", border=1, new_x="RIGHT", new_y="TOP", align="C")
        pdf.cell(20, 6, "Sum", border=1, new_x="LMARGIN", new_y="NEXT", align="C")
        
        sums = [
            ("3-6-9", nbs[0]), ("2-5-8", nbs[1]),
            ("1-4-7", nbs[2]), ("1-2-3", nbs[3]),
            ("4-5-6", nbs[4]), ("7-8-9", nbs[5]),
            ("3-5-7", nbs[6]), ("1-5-9", nbs[7])
        ]
        
        pdf.set_font("Helvetica", "", 9)
        for s_name, s_val in sums:
            pdf.set_x(70)
            pdf.cell(30, 5, s_name, border=1, new_x="RIGHT", new_y="TOP", align="C")
            pdf.cell(20, 5, str(s_val), border=1, new_x="LMARGIN", new_y="NEXT", align="C")

        # 5. Year Cycle Table
        pdf.add_page()
        pdf.set_fill_color(245, 247, 250)
        pdf.set_text_color(74, 144, 226)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, " [ Year Cycle Table ]", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_text_color(0, 0, 0)
        
        cycle_keywords = {
            1: "Beginning", 2: "Alignment", 3: "Creation", 4: "Stability", 5: "Movement",
            6: "Love", 7: "Reflection", 8: "Enrichment", 9: "Completion"
        }

        def get_cycle_rgb(cycle):
            mapping = {
                1: (255, 229, 229), 2: (255, 242, 229), 3: (255, 255, 229),
                4: (229, 255, 229), 5: (229, 255, 255), 6: (229, 242, 255),
                7: (229, 229, 255), 8: (242, 229, 255), 9: (255, 229, 242)
            }
            return mapping.get(cycle, (255, 255, 255))

        table_width = (8 + 12 + 6 + 22) * 3 + 5 * 2
        start_x = (210 - table_width) / 2

        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_x(start_x)
        for _ in range(3):
            pdf.cell(8, 6, "Age", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
            pdf.cell(12, 6, "Year", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
            pdf.cell(6, 6, "Cy", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
            pdf.cell(22, 6, "Theme", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
            pdf.cell(5, 6, "", border=0, new_x="RIGHT", new_y="TOP")
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for r in range(27):
            pdf.set_x(start_x)
            for c_idx in range(3):
                age = r + c_idx * 27
                y = res["BirthYear"] + age
                cyc = self._get_personal_year(y, res["BirthMonth"], res["BirthDay"])
                theme = cycle_keywords.get(cyc, "")
                
                rgb = get_cycle_rgb(cyc)
                pdf.set_fill_color(rgb[0], rgb[1], rgb[2])
                
                pdf.cell(8, 6, str(age), border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
                pdf.cell(12, 6, str(y), border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
                pdf.cell(6, 6, str(cyc), border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
                pdf.cell(22, 6, theme, border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
                pdf.cell(5, 6, "", border=0, new_x="RIGHT", new_y="TOP")
            pdf.ln()
            
        if ai_text:
            pdf.add_page()
            pdf.set_fill_color(245, 247, 250)
            pdf.set_text_color(74, 144, 226)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, " [ Personalized Reading ]", new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)
            
            font_filename = "NotoSansJP-Regular.ttf"
            font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP-Regular.ttf"
            
            is_valid_font = False
            if os.path.exists(font_filename):
                try:
                    with open(font_filename, "rb") as f:
                        header = f.read(4)
                        if header in (b'\x00\x01\x00\x00', b'OTTO', b'true'):
                            is_valid_font = True
                except:
                    pass
            
            if not is_valid_font:
                if os.path.exists(font_filename): os.remove(font_filename)
                try:
                    req_font = urllib.request.Request(font_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req_font) as response, open(font_filename, 'wb') as out_file:
                        out_file.write(response.read())
                    is_valid_font = True
                except Exception: pass

            if is_valid_font:
                try:
                    pdf.add_font("NotoSansJP", "", font_filename)
                    max_width = 180  
                    for line in ai_text.split('\n'):
                        line = line.strip()
                        if not line:
                            pdf.ln(3)
                            continue
                        is_heading = False
                        display_text = line
                        if line.startswith('#'):
                            is_heading = True
                            level = len(line) - len(line.lstrip('#'))
                            display_text = line.lstrip('#').strip()
                            pdf.ln(3)
                            pdf.set_text_color(74, 144, 226)
                            if level == 1: pdf.set_font("NotoSansJP", "", 14)
                            elif level == 2: pdf.set_font("NotoSansJP", "", 13)
                            else: pdf.set_font("NotoSansJP", "", 12)
                        else:
                            pdf.set_text_color(0, 0, 0)
                            pdf.set_font("NotoSansJP", "", 10)
                        current_str = ""
                        line_height = 8 if is_heading else 6
                        for char in display_text:
                            if pdf.get_string_width(current_str + char) > max_width:
                                pdf.cell(0, line_height, current_str, new_x="LMARGIN", new_y="NEXT", align="L")
                                current_str = char
                            else:
                                current_str += char
                        if current_str:
                            pdf.cell(0, line_height, current_str, new_x="LMARGIN", new_y="NEXT", align="L")
                        if is_heading:
                            pdf.set_text_color(0, 0, 0)
                            pdf.set_font("NotoSansJP", "", 10)
                except Exception:
                    pdf.set_font("Helvetica", "", 10)
                    pdf.cell(0, 6, "(Font integration error.)", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, "(Font download failed.)", new_x="LMARGIN", new_y="NEXT")

        pdf.output(filename)
        return filename

# ==========================================
# Streamlit を用いた モダン Web UI 実装
# ==========================================
st.set_page_config(page_title="Natal Chart Dashboard", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

div[data-testid="metric-container"] {
    background-color: var(--secondary-background-color);
    border: 1px solid var(--border-color);
    padding: 15px 20px;
    border-radius: 10px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s ease-in-out;
    text-align: center;
}
div[data-testid="metric-container"] > div {
    justify-content: center;
    align-items: center;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-3px);
    box-shadow: 4px 6px 12px rgba(0,0,0,0.2);
}
.section-header {
    color: #4a90e2 !important; 
    border-bottom: 2px solid #4a90e2 !important;
    padding-bottom: 8px;
    margin-top: 40px;
    margin-bottom: 20px;
    font-size: 1.6em;
    font-weight: 600;
    width: 100%;
    display: block;
}
table th, table td {
    text-align: center !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Natal Chart Dashboard")
st.write("Enter your details below to generate a comprehensive Numerology analysis.")

if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = False

with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        name_in = st.text_input("Name (e.g., Goro Sakamaki)", value="Goro Sakamaki")
    with col2:
        birth_date = st.date_input("Birthday", value=datetime(1971, 6, 25), min_value=datetime(1900, 1, 1))
        birth_in = birth_date.strftime("%Y%m%d")
    
    submitted = st.form_submit_button("Generate Dashboard")

if submitted:
    if not re.match(r'^[a-zA-Z\s]+$', name_in):
        st.error("エラー: 氏名はローマ字（アルファベット）のみで入力してください。")
    elif len(birth_in) != 8 or not birth_in.isdigit():
        st.error("エラー: 生年月日は正しく入力してください。")
    else:
        st.session_state.show_dashboard = True
        st.session_state.ai_reading = None

if st.session_state.show_dashboard:
    if len(birth_in) == 8 and birth_in.isdigit():
        with st.spinner("Analyzing your numbers..."):
            chart = NatalChart(name=name_in, birthdate=birth_in)
            report_text = chart.generate_report_text()
            res = chart.results
            c = res["Counts"]
            
            with st.expander("📄 Show Original Text Report Format", expanded=False):
                st.code(report_text, language="text")
            
            st.markdown('<div class="section-header">🧩 [ Core Numbers & Themes ]</div>', unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Birth Number", res["BirthNum"])
            c2.metric("Destiny Number", res["DestinyNum"])
            c3.metric("Soul Number", res["SoulNum"])
            c4.metric("Personality Number", res["PersoNum"])
            c5.metric("Realization Number", res["RealizNum"])
            
            st.write("") 
            
            c6, c7, c8, c9, c10 = st.columns(5)
            c6.metric("Stage Number", res["StageNum"])
            c7.metric("Challenge Number", res["ChallNum"])
            c8.metric("New Strength", res["Strengths"])
            c9.metric("Hidden Theme", res["SubTheme"])
            c10.metric("Carmic Number", res["CarmicNum"])

            st.markdown('<div class="section-header">⌛ [ Turning Point Ages ]</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("1st Turning Point", f"{res['TP'][0]} yrs")
            c2.metric("2nd Turning Point (Main)", f"{res['TP'][1]} yrs")
            c3.metric("3rd Turning Point", f"{res['TP'][2]} yrs")

            st.markdown('<div class="section-header">📅 [ Life Cycle Stages ]</div>', unsafe_allow_html=True)
            df_stages = pd.DataFrame(res["Stages"])
            df_stages.columns = ["Term", "Age", "Milestone", "Rout", "Hardships"]
            
            styled_stages = df_stages.style.set_properties(**{'text-align': 'center'}) \
                .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]) \
                .hide(axis="index")
            st.table(styled_stages)
            
            st.markdown('<div class="section-header">🔮 [ Nine Box ]</div>', unsafe_allow_html=True)
            
            col_box, col_sums = st.columns([1, 1])
            with col_box:
                html_grid = f"""
                <table style='width: 100%; max-width: 400px; text-align: center; border-collapse: separate; border-spacing: 8px;'>
                  <tr>
                    <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                      <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[3]</span><br><span style='font-size:28px; font-weight:bold; color: #4a90e2;'>{c[3]}</span>
                    </td>
                    <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                      <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[6]</span><br><span style='font-size:28px; font-weight:bold; color: #4a90e2;'>{c[6]}</span>
                    </td>
                    <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                      <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[9]</span><br><span style='font-size:28px; font-weight:bold; color: #4a90e2;'>{c[9]}</span>
                    </td>
                  </tr>
                  <tr>
                    <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                      <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[2]</span><br><span style='font-size:28px; font-weight:bold; color: #4a90e2;'>{c[2]}</span>
                    </td>
                    <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                      <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[5]</span><br><span style='font-size:28px; font-weight:bold; color: #4a90e2;'>{c[5]}</span>
                    </td>
                    <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                      <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[8]</span><br><span style='font-size:28px; font-weight:bold; color: #4a90e2;'>{c[8]}</span>
                    </td>
                  </tr>
                  <tr>
                    <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                      <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[1]</span><br><span style='font-size:28px; font-weight:bold; color: #4a90e2;'>{c[1]}</span>
                    </td>
                    <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                      <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[4]</span><br><span style='font-size:28px; font-weight:bold; color: #4a90e2;'>{c[4]}</span>
                    </td>
                    <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                      <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[7]</span><br><span style='font-size:28px; font-weight:bold; color: #4a90e2;'>{c[7]}</span>
                    </td>
                  </tr>
                </table>
                """
                st.markdown(html_grid, unsafe_allow_html=True)
                
            with col_sums:
                ma = res["MagicArray"]
                nbs = res["NineBoxSums"]
                max_val = res["NineBoxMax"] if res["NineBoxMax"] > 0 else 1
                
                sum_lines_data = [
                    {"name": "3-6-9", "str": nbs[0], "num": ma[0]},
                    {"name": "2-5-8", "str": nbs[1], "num": ma[1]},
                    {"name": "1-4-7", "str": nbs[2], "num": ma[2]},
                    {"name": "1-2-3", "str": nbs[3], "num": ma[3]},
                    {"name": "4-5-6", "str": nbs[4], "num": ma[4]},
                    {"name": "7-8-9", "str": nbs[5], "num": ma[5]},
                    {"name": "3-5-7", "str": nbs[6], "num": ma[6]},
                    {"name": "1-5-9", "str": nbs[7], "num": ma[7]}
                ]
                
                sum_html = "<table style='width:100%; border-collapse: collapse; margin-top: 10px; color: inherit;'>"
                sum_html += "<tr style='border-bottom: 2px solid var(--border-color);'><th style='padding:8px; text-align:center;'>Sum Lines</th><th style='padding:8px; text-align:center;'>Sum</th><th style='padding:8px; width:50%;'></th></tr>"
                for s in sum_lines_data:
                    bar_w = int((s["num"] / max_val) * 100) if s["str"] != "_" else 0
                    bar = f"<div style='width:{bar_w}%; background-color:#4a90e2; height:12px; border-radius:3px;'></div>" if bar_w > 0 else ""
                    sum_html += f"<tr><td style='padding:8px; border-bottom:1px solid var(--border-color); text-align:center;'>{s['name']}</td><td style='padding:8px; border-bottom:1px solid var(--border-color); text-align:center; font-weight:bold;'>{s['str']}</td><td style='padding:8px; border-bottom:1px solid var(--border-color);'>{bar}</td></tr>"
                sum_html += "</table>"
                st.markdown(sum_html, unsafe_allow_html=True)

            st.markdown('<div class="section-header">🌊 [ Year Cycle Table (Age 0 - 80) ]</div>', unsafe_allow_html=True)
            
            cycle_keywords = {
                1: "Beginning", 2: "Alignment", 3: "Creation", 4: "Stability", 5: "Movement",
                6: "Love", 7: "Reflection", 8: "Enrichment", 9: "Completion"
            }
            
            col_a, col_b, col_c = st.columns(3)
            
            def create_cycle_df(start_age, end_age):
                data = []
                for age in range(start_age, end_age):
                    y = res["BirthYear"] + age
                    cyc = chart._get_personal_year(y, res["BirthMonth"], res["BirthDay"])
                    theme = cycle_keywords.get(cyc, "")
                    data.append({"Age": age, "Year": y, "Cycle": cyc, "Theme": theme})
                return pd.DataFrame(data)

            def color_cycle(val):
                colors = {
                    1: '#ffe5e5', 2: '#fff2e5', 3: '#ffffe5', 
                    4: '#e5ffe5', 5: '#e5ffff', 6: '#e5f2ff', 
                    7: '#e5e5ff', 8: '#f2e5ff', 9: '#ffe5f2'
                }
                bg_color = colors.get(val, '')
                return f'background-color: {bg_color}; color: #000000;' if bg_color else ''

            def style_cycles(df):
                return df.style.map(color_cycle, subset=['Cycle']) \
                               .set_properties(**{'text-align': 'center'}) \
                               .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]) \
                               .hide(axis="index")

            with col_a: st.table(style_cycles(create_cycle_df(0, 27)))
            with col_b: st.table(style_cycles(create_cycle_df(27, 54)))
            with col_c: st.table(style_cycles(create_cycle_df(54, 81)))

            # --- 4. Personalized Reading ---
            st.markdown('<div class="section-header">🤖 [ Personalized Reading ]</div>', unsafe_allow_html=True)
            st.write("上記の結果に基づいたあなた専用のパーソナライズされた鑑定書を生成します。")

            try:
                api_key = str(st.secrets["GEMINI_API_KEY"]).strip()

                if st.button("✨ Generate Reading"):
                    try:
                        with open("prompt_template.txt", "r", encoding="utf-8") as f:
                            template_text = f.read()
                    except FileNotFoundError:
                        st.error("Error: 'prompt_template.txt' が見つかりません。")
                        st.stop()
                    
                    JST = timezone(timedelta(hours=+9), 'JST')
                    current_time_str = datetime.now(JST).strftime("%Y年%m月%d日")
                        
                    prompt = template_text.format(
                        name=name_in, 
                        full_report=report_text,
                        current_date=current_time_str
                    )
                    selected_model = "gemini-2.5-flash"

                    with st.spinner("鑑定士 N a b i が言葉を紡いでいます..."):
                        placeholder = st.empty()
                        full_text = ""
                        try:
                            for chunk in get_gemini_reading_stream(api_key, selected_model, prompt):
                                full_text += chunk
                                
                                temp_html = ""
                                for line in full_text.split('\n'):
                                    line = line.strip()
                                    if not line:
                                        temp_html += "<div style='height: 12px;'></div>"
                                        continue
                                    if line.startswith('#'):
                                        title_text = line.lstrip('#').strip()
                                        temp_html += f"<div style='color: #4a90e2; font-size: 1.3em; font-weight: 600; margin-top: 30px; margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 5px;'>{title_text}</div>"
                                    else:
                                        temp_html += f"<div style='margin-bottom: 8px;'>{line}</div>"
                                placeholder.markdown(f"""<div style="background-color: var(--secondary-background-color); border: 1px solid var(--border-color); padding: 30px; border-radius: 10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); text-align: left; line-height: 1.8;">{temp_html}</div>""", unsafe_allow_html=True)
                                
                            st.session_state.ai_reading = full_text
                            placeholder.empty()
                        except urllib.error.HTTPError as e:
                            try:
                                error_details = e.read().decode('utf-8')
                                st.error(f"Google API エラー (HTTP {e.code}):\n{error_details}")
                            except:
                                st.error(f"通信エラーが発生しました: HTTP {e.code}")
                        except Exception as e:
                            st.error(f"システムエラーが発生しました: {e}")

            except KeyError: st.error("Error: APIキーが設定されていません。")
            except Exception as e: st.error(f"不明なエラー: {e}")
            
            if st.session_state.get("ai_reading"):
                st.success("✨ 鑑定書の生成が完了しました！")
                formatted_html = ""
                for line in st.session_state.ai_reading.split('\n'):
                    line = line.strip()
                    if not line:
                        formatted_html += "<div style='height: 12px;'></div>"
                        continue
                    if line.startswith('#'):
                        title_text = line.lstrip('#').strip()
                        formatted_html += f"<div style='color: #4a90e2; font-size: 1.3em; font-weight: 600; margin-top: 30px; margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 5px;'>{title_text}</div>"
                    else:
                        formatted_html += f"<div style='margin-bottom: 8px;'>{line}</div>"
                st.markdown(f"""<div style="background-color: var(--secondary-background-color); border: 1px solid var(--border-color); padding: 30px; border-radius: 10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); text-align: left; line-height: 1.8;">{formatted_html}</div>""", unsafe_allow_html=True)

            # --- PDF Export セクション ---
            st.markdown('<div class="section-header">📥 [ Export Report ]</div>', unsafe_allow_html=True)
            if HAS_FPDF:
                pdf_filename = f"{name_in.replace(' ', '_')}_Graphical.pdf"
                ai_text = st.session_state.get("ai_reading", None)
                chart.export_graphical_pdf(pdf_filename, ai_text=ai_text)
                with open(pdf_filename, "rb") as pdf_file:
                    st.download_button(label="📄 Download Full Graphical PDF", data=pdf_file, file_name=pdf_filename, mime="application/pdf", use_container_width=True)
                os.remove(pdf_filename)
            else: st.warning("PDFライブラリが不足しています。")

st.markdown("""
<div style="text-align: center; color: gray; font-size: 12px; margin-top: 50px;">
    Navigated by Nabi<br>
    <a href="https://sites.google.com/view/natalchart/privacy-policy" target="_blank" style="color: gray; text-decoration: underline;">Privacy Policy</a>
</div>
""", unsafe_allow_html=True)