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
# ★設定ファイル（コントロールファイル）の読み込み
# ==========================================
def load_settings():
    settings_file = "settings.json"
    default_settings = {"enable_synastry": True}
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_settings
    else:
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=4)
        except Exception:
            pass
        return default_settings

APP_SETTINGS = load_settings()
ENABLE_SYNASTRY = APP_SETTINGS.get("enable_synastry", True)


# ==========================================
# 1. API呼び出し関数（完全修復型フェイルセーフ版）
# ==========================================
def get_gemini_reading_stream(api_key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={api_key}"
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192} 
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    
    buffer = ""
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            for line in response:
                line_str = line.decode('utf-8')
                
                if not line_str.strip():
                    continue
                    
                if line_str.startswith("data: "):
                    content = line_str[6:].strip()
                    if content == "[DONE]":
                        break
                    buffer = content
                else:
                    buffer += line_str.strip()
                    
                try:
                    chunk_json = json.loads(buffer)
                    if "candidates" in chunk_json and len(chunk_json["candidates"]) > 0:
                        cand = chunk_json["candidates"][0]
                        parts = cand.get("content", {}).get("parts", [])
                        if parts:
                            chunk_text = parts[0].get("text", "")
                            yield chunk_text.replace('*', '')
                        
                        finish_reason = cand.get("finishReason")
                        if finish_reason and finish_reason not in ("STOP", ""):
                            yield f"\n\n[⚠️AIの生成が停止しました: {finish_reason}]"
                            
                    buffer = "" 
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        yield f"\n\n[⚠️ネットワーク通信エラーが発生しました: {str(e)}]\nもう一度お試しください。"

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
        
        y_raw = sum(int(d) for d in str(b_year))
        m_raw = (b_month // 10) + (b_month % 10)
        d_raw = (b_day // 10) + (b_day % 10)

        carmic1 = y_raw + m_raw + d_raw
        def vba_reduce_once(n): return (n // 10) + (n % 10)
        carmic2 = vba_reduce_once(y_raw) + vba_reduce_once(m_raw) + vba_reduce_once(d_raw)
        
        a0 = b_year + b_month + b_day
        carmic3 = sum(int(d) for d in str(a0))
        
        carmic_0 = 0
        for c in (carmic1, carmic2, carmic3):
            if c in (13, 14, 16, 19): carmic_0 = c
        carmic_str = str(carmic_0) if carmic_0 != 0 else "-"

        raw_birth = y_raw + m_raw + d_raw
        display_birth_num = self._reduce_to_single(raw_birth)
        temp_val = raw_birth
        while temp_val >= 10:
            if temp_val in (11, 22):
                display_birth_num = temp_val
                break
            temp_val = sum(int(digit) for digit in str(temp_val))

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
        
        # 105歳対応のテキストレポート出力 (35年×3列)
        lines.append(" [ Year Cycle Table ]")
        lines.append("  Age | Year | Cyc Theme    || Age | Year | Cyc Theme    || Age | Year | Cyc Theme")
        lines.append("  " + "-" * 81)
        for r in range(35):
            row_str = ""
            for c_idx in range(3):
                age = r + c_idx * 35
                y = res["BirthYear"] + age
                cyc = self._get_personal_year(y, res["BirthMonth"], res["BirthDay"])
                theme = cycle_keywords.get(cyc, "")
                row_str += f" {age:>2} | {y} | {cyc} {theme:<10}"
                if c_idx < 2:
                    row_str += " ||"
            lines.append(f"  {row_str}")
        lines.append("=" * 75)
        return "\n".join(lines)

    def export_graphical_pdf(self, filename="Premium_Report.pdf", ai_text=None, pdf=None):
        if not HAS_FPDF: return None
        
        is_main = False
        if pdf is None:
            pdf = FPDF()
            is_main = True
            
        pdf.add_page()
        
        NAVY = (44, 62, 80)
        GOLD = (212, 175, 55)
        LIGHT_GREY = (245, 247, 250)
        BORDER_GREY = (220, 220, 220)
        TEXT_GREY = (100, 100, 100)
        
        pdf.set_fill_color(*NAVY)
        pdf.rect(0, 0, 210, 40, 'F')
        
        pdf.set_fill_color(*GOLD)
        pdf.rect(0, 40, 210, 2, 'F')
        
        pdf.set_y(12)
        pdf.set_text_color(*GOLD)
        pdf.set_font("Helvetica", "B", 22)
        pdf.cell(0, 10, "NATAL CHART ANALYSIS", new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "", 11)
        b_date_str = f"{self.results['BirthYear']} / {self.results['BirthMonth']:02} / {self.results['BirthDay']:02}"
        pdf.cell(0, 8, f"{self.raw_name.upper()}   |   {b_date_str}", new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_y(50)

        def draw_section_header(title):
            pdf.ln(4)
            y_start = pdf.get_y()
            pdf.set_fill_color(*LIGHT_GREY)
            pdf.rect(10, y_start, 190, 8, 'F')
            
            pdf.set_fill_color(*GOLD)
            pdf.rect(10, y_start, 2, 8, 'F')
            
            pdf.set_y(y_start)
            pdf.set_x(15)
            pdf.set_text_color(*NAVY)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

        draw_section_header("CORE NUMBERS & THEMES")
        res = self.results
        
        data_left = [["Birth Number", res["BirthNum"]], ["Destiny Number", res["DestinyNum"]], ["Soul Number", res["SoulNum"]], ["Personality Number", res["PersoNum"]], ["Realization Number", res["RealizNum"]]]
        data_right = [["Stage Number", res["StageNum"]], ["Challenge Number", res["ChallNum"]], ["New Strength", res["Strengths"]], ["Hidden Theme", res["SubTheme"]], ["Carmic Number", res["CarmicNum"]]]
        
        pdf.set_draw_color(*BORDER_GREY)
        y_start = pdf.get_y()
        
        for item in data_left:
            pdf.set_fill_color(*LIGHT_GREY)
            pdf.set_text_color(*TEXT_GREY)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(50, 8, f" {item[0]}", border=1, new_x="RIGHT", new_y="TOP", fill=True)
            
            pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(*NAVY)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(15, 8, str(item[1]), border=1, new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
            
        pdf.set_xy(10 + 65 + 10, y_start)
        for item in data_right:
            pdf.set_x(10 + 65 + 10)
            pdf.set_fill_color(*LIGHT_GREY)
            pdf.set_text_color(*TEXT_GREY)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(50, 8, f" {item[0]}", border=1, new_x="RIGHT", new_y="TOP", fill=True)
            
            pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(*NAVY)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(15, 8, str(item[1]), border=1, new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
        
        pdf.set_y(y_start + (8 * 5) + 2)

        draw_section_header("TURNING POINT AGES")

        y_start_tp = pdf.get_y()
        pdf.set_fill_color(*LIGHT_GREY)
        pdf.set_text_color(*TEXT_GREY)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(35, 8, " 1st Turning Point", border=1, new_x="RIGHT", new_y="TOP", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(15, 8, f"{res['TP'][0]}", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
        
        pdf.set_xy(10 + 50 + 10, y_start_tp)
        pdf.set_fill_color(*LIGHT_GREY)
        pdf.set_text_color(*TEXT_GREY)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(45, 8, " 2nd Turning Point (Main)", border=1, new_x="RIGHT", new_y="TOP", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(15, 8, f"{res['TP'][1]}", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
        
        pdf.set_xy(10 + 50 + 10 + 60 + 10, y_start_tp)
        pdf.set_fill_color(*LIGHT_GREY)
        pdf.set_text_color(*TEXT_GREY)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(35, 8, " 3rd Turning Point", border=1, new_x="RIGHT", new_y="TOP", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(15, 8, f"{res['TP'][2]}", border=1, new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
        
        draw_section_header("LIFE CYCLE STAGES")
        
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(30, 8, "Term", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
        pdf.cell(40, 8, "Age", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
        pdf.cell(30, 8, "Milestone", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
        pdf.cell(30, 8, "Rout", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
        pdf.cell(30, 8, "Hardships", border=1, new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
        
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT_GREY)
        for i, s in enumerate(res["Stages"]):
            fill_clr = True if i % 2 == 0 else False
            pdf.set_fill_color(252, 253, 255)
            
            pdf.cell(30, 8, s["term"], border=1, new_x="RIGHT", new_y="TOP", align="C", fill=fill_clr)
            pdf.cell(40, 8, s["age"], border=1, new_x="RIGHT", new_y="TOP", align="C", fill=fill_clr)
            
            pdf.set_text_color(*NAVY)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(30, 8, str(s["pin"]), border=1, new_x="RIGHT", new_y="TOP", align="C", fill=fill_clr)
            pdf.cell(30, 8, str(s["root"]), border=1, new_x="RIGHT", new_y="TOP", align="C", fill=fill_clr)
            pdf.cell(30, 8, str(s["hard"]), border=1, new_x="LMARGIN", new_y="NEXT", align="C", fill=fill_clr)
            pdf.set_text_color(*TEXT_GREY)
            pdf.set_font("Helvetica", "", 9)
        
        draw_section_header("NINE BOX ANALYSIS")
        
        c = res["Counts"]
        nbs = res["NineBoxSums"]
        y_start_nb = pdf.get_y()
        
        cell_size = 18
        for row_idx, row_nums in enumerate([[3,6,9], [2,5,8], [1,4,7]]):
            for col_idx, num in enumerate(row_nums):
                pdf.set_xy(10 + (col_idx * cell_size), y_start_nb + (row_idx * cell_size))
                pdf.set_fill_color(252, 253, 255)
                pdf.rect(pdf.get_x(), pdf.get_y(), cell_size, cell_size, 'DF')
                
                pdf.set_text_color(180, 180, 180)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_xy(10 + (col_idx * cell_size) + 2, y_start_nb + (row_idx * cell_size) + 2)
                pdf.cell(5, 5, f"[{num}]")
                
                pdf.set_text_color(*NAVY)
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_xy(10 + (col_idx * cell_size), y_start_nb + (row_idx * cell_size) + 6)
                pdf.cell(cell_size, cell_size - 6, str(c[num]), align="C")
                
        pdf.set_xy(80, y_start_nb)
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(30, 7, "Line", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
        pdf.cell(20, 7, "Sum", border=1, new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
        
        sums = [
            ("3-6-9", nbs[0]), ("2-5-8", nbs[1]), ("1-4-7", nbs[2]), ("1-2-3", nbs[3]),
            ("4-5-6", nbs[4]), ("7-8-9", nbs[5]), ("3-5-7", nbs[6]), ("1-5-9", nbs[7])
        ]
        
        pdf.set_font("Helvetica", "", 9)
        for i, (s_name, s_val) in enumerate(sums):
            pdf.set_x(80)
            fill_clr = True if i % 2 == 0 else False
            pdf.set_fill_color(252, 253, 255)
            pdf.set_text_color(*TEXT_GREY)
            pdf.cell(30, 6, s_name, border=1, new_x="RIGHT", new_y="TOP", align="C", fill=fill_clr)
            pdf.set_text_color(*NAVY)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(20, 6, str(s_val), border=1, new_x="LMARGIN", new_y="NEXT", align="C", fill=fill_clr)
            pdf.set_font("Helvetica", "", 9)

        # --- Page 2: Year Cycle (105歳対応 / 35年×3列) ---
        pdf.add_page()
        pdf.set_draw_color(*BORDER_GREY)
        draw_section_header("YEAR CYCLE TABLE (Age 0 - 104)")
        
        cycle_keywords = {
            1: "Beginning", 2: "Alignment", 3: "Creation", 4: "Stability", 5: "Movement",
            6: "Love", 7: "Reflection", 8: "Enrichment", 9: "Completion"
        }

        def get_cycle_rgb(cycle):
            mapping = {
                1: (255, 240, 240), 2: (255, 248, 240), 3: (255, 255, 240),
                4: (240, 255, 240), 5: (240, 255, 255), 6: (240, 248, 255),
                7: (240, 240, 255), 8: (248, 240, 255), 9: (255, 240, 248)
            }
            return mapping.get(cycle, (255, 255, 255))

        # 元の美しい3列幅設定を復元
        col_w_age = 8
        col_w_year = 12
        col_w_cyc = 6
        col_w_theme = 22
        col_w_gap = 5
        table_width = (col_w_age + col_w_year + col_w_cyc + col_w_theme) * 3 + col_w_gap * 2
        start_x = (210 - table_width) / 2

        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_x(start_x)
        for i in range(3):
            pdf.cell(col_w_age, 6, "Age", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
            pdf.cell(col_w_year, 6, "Year", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
            pdf.cell(col_w_cyc, 6, "Cy", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
            pdf.cell(col_w_theme, 6, "Theme", border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
            if i < 2:
                pdf.cell(col_w_gap, 6, "", border=0, new_x="RIGHT", new_y="TOP")
        pdf.ln()

        pdf.set_text_color(*TEXT_GREY)
        pdf.set_font("Helvetica", "", 8)
        # 35行で出力
        for r in range(35):
            pdf.set_x(start_x)
            for c_idx in range(3):
                age = r + c_idx * 35
                y = res["BirthYear"] + age
                cyc = self._get_personal_year(y, res["BirthMonth"], res["BirthDay"])
                theme = cycle_keywords.get(cyc, "")
                
                rgb = get_cycle_rgb(cyc)
                pdf.set_fill_color(rgb[0], rgb[1], rgb[2])
                
                pdf.cell(col_w_age, 5, str(age), border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
                pdf.cell(col_w_year, 5, str(y), border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
                
                pdf.set_text_color(*NAVY)
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(col_w_cyc, 5, str(cyc), border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
                
                pdf.set_text_color(*TEXT_GREY)
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(col_w_theme, 5, theme, border=1, new_x="RIGHT", new_y="TOP", align="C", fill=True)
                
                if c_idx < 2:
                    pdf.cell(col_w_gap, 5, "", border=0, new_x="RIGHT", new_y="TOP")
            pdf.ln()
            
        if ai_text:
            pdf.add_page()
            draw_section_header("PERSONALIZED READING")
            
            font_filename = "NotoSansJP-Regular.ttf"
            font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP-Regular.ttf"
            
            is_valid_font = False
            if os.path.exists(font_filename):
                try:
                    with open(font_filename, "rb") as f:
                        header = f.read(4)
                        if header in (b'\x00\x01\x00\x00', b'OTTO', b'true'):
                            is_valid_font = True
                except: pass
            
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
                            pdf.ln(4)
                            continue
                        
                        is_heading = False
                        display_text = line
                        if line.startswith('#'):
                            is_heading = True
                            level = len(line) - len(line.lstrip('#'))
                            display_text = line.lstrip('#').strip()
                            pdf.ln(4)
                            pdf.set_text_color(*GOLD)
                            if level == 1: pdf.set_font("NotoSansJP", "", 14)
                            elif level == 2: pdf.set_font("NotoSansJP", "", 13)
                            else: pdf.set_font("NotoSansJP", "", 11)
                        else:
                            pdf.set_text_color(50, 50, 50)
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
                except Exception:
                    pdf.set_font("Helvetica", "", 10)
                    pdf.cell(0, 6, "(Font integration error.)", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, "(Font download failed.)", new_x="LMARGIN", new_y="NEXT")

        pdf.set_y(-15)
        pdf.set_text_color(180, 180, 180)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 10, "Navigated by Nabi", align="C")

        if is_main:
            pdf.output(filename)
            return filename
        return pdf


# ==========================================
# UI レンダリング用関数
# ==========================================
def render_dashboard(chart1, chart2=None):
    res1 = chart1.results
    c1 = res1["Counts"]
    
    res2 = chart2.results if chart2 else None
    c2 = res2["Counts"] if chart2 else None

    def draw_metric(col, label, key, is_tp=False):
        val1 = f"{res1['TP'][key]} yrs" if is_tp else str(res1[key])
        val2_html = ""
        if res2:
            val2 = f"{res2['TP'][key]} yrs" if is_tp else str(res2[key])
            val2_html = f"<span class='metric-value-sub'>({val2})</span>"
        
        html = f"""
        <div class="custom-metric">
            <div class="metric-label">{label}</div>
            <div><span class="metric-value-main">{val1}</span>{val2_html}</div>
        </div>
        """
        col.markdown(html, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">[ Core Numbers & Themes ]</div>', unsafe_allow_html=True)
    
    c1_col, c2_col, c3_col, c4_col, c5_col = st.columns(5)
    draw_metric(c1_col, "Birth Number", "BirthNum")
    draw_metric(c2_col, "Destiny Number", "DestinyNum")
    draw_metric(c3_col, "Soul Number", "SoulNum")
    draw_metric(c4_col, "Personality Number", "PersoNum")
    draw_metric(c5_col, "Realization Number", "RealizNum")
    
    st.write("") 
    
    c6_col, c7_col, c8_col, c9_col, c10_col = st.columns(5)
    draw_metric(c6_col, "Stage Number", "StageNum")
    draw_metric(c7_col, "Challenge Number", "ChallNum")
    draw_metric(c8_col, "New Strength", "Strengths")
    draw_metric(c9_col, "Hidden Theme", "SubTheme")
    draw_metric(c10_col, "Carmic Number", "CarmicNum")

    st.markdown('<div class="section-header">[ Turning Point Ages ]</div>', unsafe_allow_html=True)
    c1_tp, c2_tp, c3_tp = st.columns(3)
    draw_metric(c1_tp, "1st Turning Point", 0, is_tp=True)
    draw_metric(c2_tp, "2nd Turning Point (Main)", 1, is_tp=True)
    draw_metric(c3_tp, "3rd Turning Point", 2, is_tp=True)

    st.markdown('<div class="section-header">[ Life Cycle Stages ]</div>', unsafe_allow_html=True)
    
    stages_data = []
    for i in range(len(res1["Stages"])):
        s1 = res1["Stages"][i]
        s_dict = {"Term": s1["term"], "Age": s1["age"]}
        if res2:
            s2 = res2["Stages"][i]
            s_dict["Milestone"] = f"{s1['pin']} ({s2['pin']})"
            s_dict["Rout"] = f"{s1['root']} ({s2['root']})"
            s_dict["Hardships"] = f"{s1['hard']} ({s2['hard']})"
        else:
            s_dict["Milestone"] = str(s1['pin'])
            s_dict["Rout"] = str(s1['root'])
            s_dict["Hardships"] = str(s1['hard'])
        stages_data.append(s_dict)
        
    df_stages = pd.DataFrame(stages_data)
    styled_stages = df_stages.style.set_properties(**{'text-align': 'center'}) \
        .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]) \
        .hide(axis="index")
    st.table(styled_stages)
    
    st.markdown('<div class="section-header">[ Nine Box ]</div>', unsafe_allow_html=True)
    
    def get_c_html(num):
        main_c = c1[num]
        sub_c = f" <span style='font-size:14px; color:gray; font-weight:normal;'>({c2[num]})</span>" if c2 else ""
        return f"<span style='font-size:28px; font-weight:bold; color: #4a90e2;'>{main_c}</span>{sub_c}"

    col_box, col_sums = st.columns([1, 1])
    with col_box:
        html_grid = f"""
        <table style='width: 100%; max-width: 400px; text-align: center; border-collapse: separate; border-spacing: 8px;'>
            <tr>
            <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[3]</span><br>{get_c_html(3)}
            </td>
            <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[6]</span><br>{get_c_html(6)}
            </td>
            <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[9]</span><br>{get_c_html(9)}
            </td>
            </tr>
            <tr>
            <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[2]</span><br>{get_c_html(2)}
            </td>
            <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[5]</span><br>{get_c_html(5)}
            </td>
            <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[8]</span><br>{get_c_html(8)}
            </td>
            </tr>
            <tr>
            <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[1]</span><br>{get_c_html(1)}
            </td>
            <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[4]</span><br>{get_c_html(4)}
            </td>
            <td style='border-radius: 10px; padding: 20px; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); box-shadow: 1px 1px 4px rgba(0,0,0,0.05); color: inherit;'>
                <span style='opacity:0.7; font-size:14px; font-weight:bold;'>[7]</span><br>{get_c_html(7)}
            </td>
            </tr>
        </table>
        """
        st.markdown(html_grid, unsafe_allow_html=True)
        
    with col_sums:
        ma1 = res1["MagicArray"]
        nbs1 = res1["NineBoxSums"]
        max_val1 = res1["NineBoxMax"] if res1["NineBoxMax"] > 0 else 1
        
        nbs2 = res2["NineBoxSums"] if res2 else None
        
        sum_lines_data = [
            {"name": "3-6-9", "str1": nbs1[0], "str2": nbs2[0] if nbs2 else "", "num": ma1[0]},
            {"name": "2-5-8", "str1": nbs1[1], "str2": nbs2[1] if nbs2 else "", "num": ma1[1]},
            {"name": "1-4-7", "str1": nbs1[2], "str2": nbs2[2] if nbs2 else "", "num": ma1[2]},
            {"name": "1-2-3", "str1": nbs1[3], "str2": nbs2[3] if nbs2 else "", "num": ma1[3]},
            {"name": "4-5-6", "str1": nbs1[4], "str2": nbs2[4] if nbs2 else "", "num": ma1[4]},
            {"name": "7-8-9", "str1": nbs1[5], "str2": nbs2[5] if nbs2 else "", "num": ma1[5]},
            {"name": "3-5-7", "str1": nbs1[6], "str2": nbs2[6] if nbs2 else "", "num": ma1[6]},
            {"name": "1-5-9", "str1": nbs1[7], "str2": nbs2[7] if nbs2 else "", "num": ma1[7]}
        ]
        
        sum_html = "<table style='width:100%; border-collapse: collapse; margin-top: 10px; color: inherit;'>"
        sum_html += "<tr style='border-bottom: 2px solid var(--border-color);'><th style='padding:8px; text-align:center;'>Sum Lines</th><th style='padding:8px; text-align:center;'>Sum</th><th style='padding:8px; width:50%;'></th></tr>"
        for s in sum_lines_data:
            bar_w = int((s["num"] / max_val1) * 100) if s["str1"] != "_" else 0
            bar = f"<div style='width:{bar_w}%; background-color:#4a90e2; height:12px; border-radius:3px; transform-origin: left; animation: expandBar 1.2s cubic-bezier(0.1, 0.7, 0.1, 1) both 0.5s;'></div>" if bar_w > 0 else ""
            
            sub_str_html = f" <span style='font-size:12px; color:gray; font-weight:normal;'>({s['str2']})</span>" if s['str2'] else ""
            sum_html += f"<tr><td style='padding:8px; border-bottom:1px solid var(--border-color); text-align:center;'>{s['name']}</td><td style='padding:8px; border-bottom:1px solid var(--border-color); text-align:center; font-weight:bold;'>{s['str1']}{sub_str_html}</td><td style='padding:8px; border-bottom:1px solid var(--border-color);'>{bar}</td></tr>"
        sum_html += "</table>"
        st.markdown(sum_html, unsafe_allow_html=True)

    st.markdown('<div class="section-header">[ Year Cycle Table (Age 0 - 104) ]</div>', unsafe_allow_html=True)
    
    cycle_keywords = {
        1: "Beginning", 2: "Alignment", 3: "Creation", 4: "Stability", 5: "Movement",
        6: "Love", 7: "Reflection", 8: "Enrichment", 9: "Completion"
    }
    
    # 3列のレイアウトに戻し、1列を35年に変更 (35年 × 3列 = 105歳まで)
    col_a, col_b, col_c = st.columns(3)
    
    def create_cycle_df(start_age, end_age):
        data = []
        for age in range(start_age, end_age):
            y = res1["BirthYear"] + age
            cyc1 = chart1._get_personal_year(y, res1["BirthMonth"], res1["BirthDay"])
            theme1 = cycle_keywords.get(cyc1, "")
            
            if chart2:
                cyc2 = chart2._get_personal_year(y, res2["BirthMonth"], res2["BirthDay"])
                cyc_str = f"{cyc1} ({cyc2})"
            else:
                cyc_str = str(cyc1)
                
            data.append({"Age": age, "Year": y, "Cycle": cyc_str, "Theme": theme1})
        return pd.DataFrame(data)

    def color_cycle(val):
        try:
            main_val = int(str(val).split(' ')[0])
        except:
            main_val = val
            
        colors = {
            1: '#ffe5e5', 2: '#fff2e5', 3: '#ffffe5', 
            4: '#e5ffe5', 5: '#e5ffff', 6: '#e5f2ff', 
            7: '#e5e5ff', 8: '#f2e5ff', 9: '#ffe5f2'
        }
        bg_color = colors.get(main_val, '')
        return f'background-color: {bg_color}; color: #000000;' if bg_color else ''

    def style_cycles(df):
        return df.style.map(color_cycle, subset=['Cycle']) \
                       .set_properties(**{'text-align': 'center'}) \
                       .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]) \
                       .hide(axis="index")

    with col_a: st.table(style_cycles(create_cycle_df(0, 35)))
    with col_b: st.table(style_cycles(create_cycle_df(35, 70)))
    with col_c: st.table(style_cycles(create_cycle_df(70, 105)))


# ==========================================
# Streamlit を用いた モダン Web UI 実装
# ==========================================
st.set_page_config(page_title="Natal Chart Dashboard", layout="wide")

st.markdown("""
<style>
header { visibility: hidden !important; display: none !important; }
footer { visibility: hidden !important; display: none !important; }
#MainMenu { visibility: hidden !important; display: none !important; }
.stApp > header { display: none !important; }
.stApp > footer { display: none !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stFooter"] { display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
[class^="viewerBadge"], [class*="viewerBadge"] { display: none !important; opacity: 0 !important; z-index: -9999 !important; pointer-events: none !important; }
[class^="manageAppBadge"], [class*="manageAppBadge"] { display: none !important; opacity: 0 !important; z-index: -9999 !important; pointer-events: none !important; }
div[style*="position: fixed"][style*="bottom"] { display: none !important; opacity: 0 !important; z-index: -9999 !important; pointer-events: none !important; }
div[style*="position: absolute"][style*="bottom"] { display: none !important; opacity: 0 !important; z-index: -9999 !important; pointer-events: none !important; }
a[href*="streamlit.io"] { display: none !important; visibility: hidden !important; opacity: 0 !important; pointer-events: none !important; }
a[title="Fullscreen"], svg[title="Fullscreen"], button[title="Fullscreen"] { display: none !important; }
[data-testid="stBottom"], [data-testid="stEmbedFooter"] { display: none !important; height: 0 !important; margin: 0 !important; padding: 0 !important; }
.block-container { padding-bottom: 1rem !important; margin-bottom: 0rem !important; }

button[kind="tertiary"], button[kind="tertiary"] p {
    color: gray !important; font-size: 12px !important; font-weight: normal !important; font-family: inherit !important;
}
button[kind="tertiary"]:hover p { text-decoration: underline !important; }

.custom-metric {
    background-color: var(--secondary-background-color); border: 1px solid var(--border-color); padding: 15px 20px;
    border-radius: 10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); transition: transform 0.2s ease-in-out; text-align: center;
    margin-bottom: 1rem; animation: fadeInUp 0.7s ease-out both 0.15s;
}
.custom-metric:hover { transform: translateY(-3px); box-shadow: 4px 6px 12px rgba(0,0,0,0.2); }
.metric-label { font-size: 14px; color: gray; margin-bottom: 4px; }
.metric-value-main { font-size: 1.8rem; color: var(--text-color); }
.metric-value-sub { font-size: 1rem; color: gray; margin-left: 8px; }

.section-header {
    color: #4a90e2 !important; border-bottom: 2px solid #4a90e2 !important; padding-bottom: 8px; margin-top: 40px; margin-bottom: 20px;
    font-size: 1.6em; font-weight: 600; width: 100%; display: block; animation: fadeInUp 0.7s ease-out both;
}
table th, table td { text-align: center !important; }

@keyframes fadeInUp { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
@keyframes expandBar { 0% { transform: scaleX(0); } 100% { transform: scaleX(1); } }

div[data-testid="stTable"] { animation: fadeInUp 0.7s ease-out both 0.3s; }
table { animation: fadeInUp 0.7s ease-out both 0.2s; }
[data-testid="stTabs"] button { font-size: 1.1em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.dialog("Privacy Policy")
def show_privacy_policy():
    try:
        with open("privacy_policy.txt", "r", encoding="utf-8") as f:
            policy_text = f.read()
        st.markdown(policy_text)
    except FileNotFoundError:
        st.error("プライバシーポリシーのファイルが見つかりません。")

st.title("Natal Chart Dashboard")

if ENABLE_SYNASTRY:
    st.write("Enter details below to generate a comprehensive Numerology analysis. (Optional: Add a 2nd person for Synastry)")
else:
    st.write("Enter your details below to generate a comprehensive Numerology analysis.")

if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = False

with st.form("input_form"):
    JST = timezone(timedelta(hours=+9), 'JST')
    current_year = datetime.now(JST).year
    min_date = datetime(current_year - 100, 1, 1).date()
    max_date = datetime(current_year, 12, 31).date()
    
    if ENABLE_SYNASTRY:
        st.markdown("##### 👤 Person 1 (Required)")
        
    col1, col2 = st.columns(2)
    with col1:
        name_in = st.text_input("Name (e.g., Taro Yamada)", value="")
    with col2:
        birth_date = st.date_input("Birthday", value=datetime(2000, 1, 1), min_value=min_date, max_value=max_date, key="bd1")
        
    name2_in = ""
    birth2_date = None
    
    if ENABLE_SYNASTRY:
        st.markdown("##### 👥 Person 2 (Optional - For Synastry)")
        col3, col4 = st.columns(2)
        with col3:
            name2_in = st.text_input("Name 2 (Optional)", value="")
        with col4:
            birth2_date = st.date_input("Birthday 2", value=datetime(2000, 1, 1), min_value=min_date, max_value=max_date, key="bd2")
    
    submitted = st.form_submit_button("Generate Dashboard")

if submitted:
    valid = True
    if not re.match(r'^[a-zA-Z\s]+$', name_in):
        st.error("エラー: 1人目の氏名はローマ字（アルファベット）のみで入力してください。")
        valid = False
        
    if name2_in:
        if not re.match(r'^[a-zA-Z\s]+$', name2_in):
            st.error("エラー: 2人目の氏名もローマ字（アルファベット）のみで入力してください。")
            valid = False
            
    if valid:
        st.session_state.show_dashboard = True
        st.session_state.ai_reading = None

if st.session_state.show_dashboard:
    birth_in = birth_date.strftime("%Y%m%d")
    birth2_in = birth2_date.strftime("%Y%m%d") if name2_in else None
    
    if len(birth_in) == 8 and birth_in.isdigit():
        with st.spinner("Analyzing numbers..."):
            chart1 = NatalChart(name=name_in, birthdate=birth_in)
            chart2 = NatalChart(name=name2_in, birthdate=birth2_in) if name2_in else None
            
            report_text = chart1.generate_report_text()
            if chart2:
                report_text += "\n\n" + chart2.generate_report_text()
            
            with st.expander("Show Original Text Report Format", expanded=False):
                st.code(report_text, language="text")
            
            if chart2:
                tab1, tab2 = st.tabs([f"👤 {name_in.upper()}", f"👥 {name2_in.upper()}"])
                with tab1:
                    render_dashboard(chart1, chart2)
                with tab2:
                    render_dashboard(chart2, chart1)
            else:
                render_dashboard(chart1)

            st.markdown('<div class="section-header">[ Personalized Reading ]</div>', unsafe_allow_html=True)
            if chart2:
                st.write("2名分のデータに基づいた相性診断（Synastry Reading）を含めた鑑定書を生成します。")
            else:
                st.write("上記の結果に基づいたあなた専用のパーソナライズされた鑑定書を生成します。")

            try:
                api_key = str(st.secrets["GEMINI_API_KEY"]).strip()

                if st.button("Generate Reading"):
                    try:
                        with open("prompt_template.txt", "r", encoding="utf-8") as f:
                            template_text = f.read()
                    except FileNotFoundError:
                        st.error("Error: 'prompt_template.txt' が見つかりません。")
                        st.stop()
                    
                    JST = timezone(timedelta(hours=+9), 'JST')
                    current_time_str = datetime.now(JST).strftime("%Y年%m月%d日")
                        
                    prompt_name = name_in if not chart2 else f"{name_in} & {name2_in}"
                    prompt = template_text.format(
                        name=prompt_name, 
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
                                    
                                    safe_line = line.replace("<", "&lt;").replace(">", "&gt;")
                                    
                                    if safe_line.startswith('#'):
                                        title_text = safe_line.lstrip('#').strip()
                                        temp_html += f"<div style='color: #4a90e2; font-size: 1.3em; font-weight: 600; margin-top: 30px; margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 5px;'>{title_text}</div>"
                                    else:
                                        temp_html += f"<div style='margin-bottom: 8px;'>{safe_line}</div>"
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
                st.success("鑑定書の生成が完了しました！")
                formatted_html = ""
                for line in st.session_state.ai_reading.split('\n'):
                    line = line.strip()
                    if not line:
                        formatted_html += "<div style='height: 12px;'></div>"
                        continue
                        
                    safe_line = line.replace("<", "&lt;").replace(">", "&gt;")
                    
                    if safe_line.startswith('#'):
                        title_text = safe_line.lstrip('#').strip()
                        formatted_html += f"<div style='color: #4a90e2; font-size: 1.3em; font-weight: 600; margin-top: 30px; margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 5px;'>{title_text}</div>"
                    else:
                        formatted_html += f"<div style='margin-bottom: 8px;'>{safe_line}</div>"
                st.markdown(f"""<div style="background-color: var(--secondary-background-color); border: 1px solid var(--border-color); padding: 30px; border-radius: 10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); text-align: left; line-height: 1.8;">{formatted_html}</div>""", unsafe_allow_html=True)

            # --- PDF Export セクション ---
            st.markdown('<div class="section-header">[ Export Report ]</div>', unsafe_allow_html=True)
            if HAS_FPDF:
                pdf_filename = f"{name_in.replace(' ', '_')}_Premium_Report.pdf" if not chart2 else "Synastry_Premium_Report.pdf"
                ai_text = st.session_state.get("ai_reading", None)
                
                pdf = FPDF()
                if chart2:
                    chart1.export_graphical_pdf(pdf=pdf)
                    chart2.export_graphical_pdf(pdf=pdf, ai_text=ai_text)
                else:
                    chart1.export_graphical_pdf(pdf=pdf, ai_text=ai_text)
                    
                pdf.output(pdf_filename)
                
                with open(pdf_filename, "rb") as pdf_file:
                    st.download_button(label="Download Premium PDF Report", data=pdf_file, file_name=pdf_filename, mime="application/pdf", use_container_width=True)
                os.remove(pdf_filename)
            else: st.warning("PDFライブラリが不足しています。")

st.markdown("""
<div style="text-align: center; color: gray; font-size: 12px; margin-top: 50px; margin-bottom: 10px;">
    Navigated by Nabi
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("Privacy Policy", type="tertiary", use_container_width=True):
        show_privacy_policy()