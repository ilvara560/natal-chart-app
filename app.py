import os
import streamlit as st
import pandas as pd

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

# ==========================================
# ロジック・テキスト出力・PDF出力は「完全」に維持
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
        y_num = self._reduce_to_single(sum(int(d) for d in str(b_year)))
        m_num, d_num = self._reduce_to_single(b_month), self._reduce_to_single(b_day)

        birth_num = self._reduce_to_single(y_num + m_num + d_num)
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

        self.results = {
            "BirthYear": b_year, "BirthMonth": b_month, "BirthDay": b_day,
            "BirthNum": birth_num, "DestinyNum": destiny_num, "SoulNum": soul_num, "PersoNum": perso_num, "RealizNum": realiz_num,
            "StageNum": stage_num, "ChallNum": chall_num, "Strengths": strengths, "SubTheme": sub_theme,
            "TP": [tp1, tp2, tp3], "Counts": counts,
            "Stages": [
                {"term": "1st Stage", "age": f"0 ~ {s1_e}", "pin": pin[0], "root": roots[0], "hard": hards[0]},
                {"term": "2nd Stage", "age": f"{s1_e+1} ~ {s2_e}", "pin": pin[1], "root": roots[1], "hard": hards[1]},
                {"term": "3rd Stage", "age": f"{s2_e+1} ~ {s3_e}", "pin": pin[2], "root": roots[2], "hard": hards[2]},
                {"term": "4th Stage", "age": f"{s3_e+1} ~   ", "pin": pin[3], "root": roots[3], "hard": hards[3]}
            ]
        }

    def generate_report_text(self) -> str:
        res, c = self.results, self.results["Counts"]
        lines = ["=" * 75, " " * 24 + "NATAL CHART ANALYSIS REPORT", "=" * 75]
        lines.append(f" Name      : {self.raw_name.upper()}")
        lines.append(f" Birthdate : {res['BirthYear']}/{res['BirthMonth']:02}/{res['BirthDay']:02}")
        lines.append("-" * 75)
        # 統合された Core Numbers & Themes
        lines.append(" [ Core Numbers & Themes ]")
        lines.append(f"  Birth Number       : {res['BirthNum']}")
        lines.append(f"  Destiny Number     : {res['DestinyNum']}")
        lines.append(f"  Soul Number        : {res['SoulNum']}")
        lines.append(f"  Personality Number : {res['PersoNum']}")
        lines.append(f"  Realization Number : {res['RealizNum']}")
        lines.append(f"  Stage Number       : {res['StageNum']}")
        lines.append(f"  Challenge Number   : {res['ChallNum']}")
        lines.append(f"  New Strengths      : {res['Strengths']}")
        lines.append(f"  Sub Theme          : {res['SubTheme']}")
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
        lines.append(" [ Nine Box (Magic Array) ]")
        lines.append("  (Character Counts in Name)\n")
        lines.append("       [3] [6] [9]      Sum Lines:")
        lines.append(f"        {c[3]}   {c[6]}   {c[9]}       3-6-9 : {c[3]+c[6]+c[9]}")
        lines.append(f"       [2] [5] [8]      2-5-8 : {c[2]+c[5]+c[8]}")
        lines.append(f"        {c[1]}   {c[4]}   {c[7]}       1-4-7 : {c[1]+c[4]+c[7]}")
        lines.append(f"       [1] [4] [7]      1-2-3 : {c[1]+c[2]+c[3]}")
        lines.append(f"        {c[1]}   {c[4]}   {c[7]}       4-5-6 : {c[4]+c[5]+c[6]}")
        lines.append(f"                        7-8-9 : {c[7]+c[8]+c[9]}")
        lines.append(f"                        3-5-7 : {c[3]+c[5]+c[7]}")
        lines.append(f"                        1-5-9 : {c[1]+c[5]+c[9]}")
        lines.append("-" * 75)
        lines.append(" [ Cycle 1-9 Status ]")
        lines.append("  1: Beginning   2: Alignment   3: Creation   4: Stability   5: Movement")
        lines.append("  6: Love        7: Refrection  8: Enrich     9: Completion")
        lines.append("-" * 75)
        
        cycle_keywords = {
            1: "Beginning", 2: "Alignment", 3: "Creation", 4: "Stability", 5: "Movement",
            6: "Love", 7: "Refrection", 8: "Enrich", 9: "Completion"
        }
        lines.append(" [ Yearly Cycle Table ]")
        lines.append("  Age | Year | Cycle - Theme      || Age | Year | Cycle - Theme")
        lines.append("  " + "-" * 67)
        for i in range(0, 81, 2):
            row_str = ""
            for j in range(2):
                age = i + j
                if age > 80: break
                y = res["BirthYear"] + age
                cyc = self._get_personal_year(y, res["BirthMonth"], res["BirthDay"])
                theme = cycle_keywords.get(cyc, "")
                row_str += f" {age:>2} | {y} |   {cyc} - {theme:<10} "
                if j < 1 and (age + 1) <= 80:
                    row_str += "||"
            lines.append(f"  {row_str}")
        lines.append("=" * 75)
        return "\n".join(lines)

    def export_graphical_pdf(self, filename="Graphical_Report.pdf"):
        if not HAS_FPDF: return None
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "NATAL CHART ANALYSIS REPORT", ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        b_date_str = f"{self.results['BirthYear']}{self.results['BirthMonth']:02}{self.results['BirthDay']:02}"
        pdf.cell(0, 10, f"Name: {self.raw_name.upper()}  |  Birthdate: {b_date_str}", ln=True, align="C")
        pdf.ln(5)

        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, " [ Core Numbers & Themes ]", ln=True, fill=True)
        pdf.set_font("Helvetica", "", 10)
        res = self.results
        
        data_left = [["Birth Number", res["BirthNum"]], ["Destiny Number", res["DestinyNum"]], ["Soul Number", res["SoulNum"]], ["Personality Number", res["PersoNum"]], ["Realization Number", res["RealizNum"]]]
        data_right = [["Stage Number", res["StageNum"]], ["Challenge Number", res["ChallNum"]], ["New Strengths", res["Strengths"]], ["Sub Theme", res["SubTheme"]]]
        
        y_start = pdf.get_y()
        for item in data_left:
            pdf.cell(50, 7, item[0], border=1)
            pdf.cell(15, 7, str(item[1]), border=1, ln=True, align="C")
        
        pdf.set_xy(10 + 65 + 10, y_start)
        for item in data_right:
            pdf.set_x(10 + 65 + 10)
            pdf.cell(50, 7, item[0], border=1)
            pdf.cell(15, 7, str(item[1]), border=1, ln=True, align="C")
        
        pdf.set_y(y_start + (7 * 5) + 5)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f" [ Turning Point Ages ]  1st: {res['TP'][0]} yrs   |   2nd (Main): {res['TP'][1]} yrs   |   3rd: {res['TP'][2]} yrs", ln=True)
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f" [ Life Cycle Stages ]", ln=True, fill=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(30, 7, "Term", 1, 0, "C")
        pdf.cell(40, 7, "Age Range", 1, 0, "C")
        pdf.cell(30, 7, "Milestone", 1, 0, "C")
        pdf.cell(30, 7, "Rout", 1, 0, "C")
        pdf.cell(30, 7, "Hardships", 1, 1, "C")
        pdf.set_font("Helvetica", "", 9)
        for s in res["Stages"]:
            pdf.cell(30, 7, s["term"], 1)
            pdf.cell(40, 7, s["age"], 1, 0, "C")
            pdf.cell(30, 7, str(s["pin"]), 1, 0, "C")
            pdf.cell(30, 7, str(s["root"]), 1, 0, "C")
            pdf.cell(30, 7, str(s["hard"]), 1, 1, "C")
        
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, " [ Nine Box (Magic Array) ]", ln=True, fill=True)
        pdf.ln(2)
        
        c = res["Counts"]
        y_start_nb = pdf.get_y()
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(15, 6, "[3]", 1, 0, "C")
        pdf.cell(15, 6, "[6]", 1, 0, "C")
        pdf.cell(15, 6, "[9]", 1, 1, "C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(15, 6, str(c[3]), 1, 0, "C")
        pdf.cell(15, 6, str(c[6]), 1, 0, "C")
        pdf.cell(15, 6, str(c[9]), 1, 1, "C")
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(15, 6, "[2]", 1, 0, "C")
        pdf.cell(15, 6, "[5]", 1, 0, "C")
        pdf.cell(15, 6, "[8]", 1, 1, "C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(15, 6, str(c[2]), 1, 0, "C")
        pdf.cell(15, 6, str(c[5]), 1, 0, "C")
        pdf.cell(15, 6, str(c[8]), 1, 1, "C")
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(15, 6, "[1]", 1, 0, "C")
        pdf.cell(15, 6, "[4]", 1, 0, "C")
        pdf.cell(15, 6, "[7]", 1, 1, "C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(15, 6, str(c[1]), 1, 0, "C")
        pdf.cell(15, 6, str(c[4]), 1, 0, "C")
        pdf.cell(15, 6, str(c[7]), 1, 1, "C")

        pdf.set_xy(70, y_start_nb)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(30, 6, "Sum Lines", 1, 0, "C")
        pdf.cell(20, 6, "Sum", 1, 1, "C")
        
        sums = [
            ("3-6-9", c[3]+c[6]+c[9]), ("2-5-8", c[2]+c[5]+c[8]),
            ("1-4-7", c[1]+c[4]+c[7]), ("1-2-3", c[1]+c[2]+c[3]),
            ("4-5-6", c[4]+c[5]+c[6]), ("7-8-9", c[7]+c[8]+c[9]),
            ("3-5-7", c[3]+c[5]+c[7]), ("1-5-9", c[1]+c[5]+c[9])
        ]
        
        pdf.set_font("Helvetica", "", 9)
        for s_name, s_val in sums:
            pdf.set_x(70)
            pdf.cell(30, 5, s_name, 1, 0, "C")
            pdf.cell(20, 5, str(s_val), 1, 1, "C")

        pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, " [ Yearly Cycle Table ]", ln=True, fill=True)
        
        cycle_keywords = {
            1: "Beginning", 2: "Alignment", 3: "Creation", 4: "Stability", 5: "Movement",
            6: "Love", 7: "Refrection", 8: "Enrich", 9: "Completion"
        }

        table_width = (8 + 12 + 6 + 22) * 3 + 5 * 2
        start_x = (210 - table_width) / 2

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_x(start_x)
        for _ in range(3):
            pdf.cell(8, 6, "Age", 1, 0, "C")
            pdf.cell(12, 6, "Year", 1, 0, "C")
            pdf.cell(6, 6, "Cy", 1, 0, "C")
            pdf.cell(22, 6, "Theme", 1, 0, "C")
            pdf.cell(5, 6, "", 0, 0)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for i in range(0, 81, 3):
            pdf.set_x(start_x)
            for j in range(3):
                age = i + j
                if age > 80:
                    break
                y = res["BirthYear"] + age
                cyc = self._get_personal_year(y, res["BirthMonth"], res["BirthDay"])
                theme = cycle_keywords.get(cyc, "")
                pdf.cell(8, 6, str(age), 1, 0, "C")
                pdf.cell(12, 6, str(y), 1, 0, "C")
                pdf.cell(6, 6, str(cyc), 1, 0, "C")
                pdf.cell(22, 6, theme, 1, 0, "C")
                pdf.cell(5, 6, "", 0, 0)
            pdf.ln()

        pdf.output(filename)
        return filename

# ==========================================
# Streamlit を用いた モダン Web UI 実装
# ==========================================
st.set_page_config(page_title="Natal Chart Dashboard", layout="wide")

# CSSによる全体的な装飾
st.markdown("""
<style>
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

st.title("🌟 Natal Chart Web Dashboard")
st.write("Enter your details below to generate a comprehensive Numerology analysis.")

with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        name_in = st.text_input("Name (e.g., Goro Sakamaki)", value="Goro Sakamaki")
    with col2:
        birth_in = st.text_input("Birthday (YYYYMMDD)", value="19710625")
    
    submitted = st.form_submit_button("Generate Dashboard")

if submitted:
    if len(birth_in) == 8 and birth_in.isdigit():
        with st.spinner("Analyzing your numbers..."):
            chart = NatalChart(name=name_in, birthdate=birth_in)
            report_text = chart.generate_report_text()
            res = chart.results
            c = res["Counts"]
            
            # --- 1. テキストフォーマット ---
            with st.expander("📄 Show Original Text Report Format", expanded=False):
                st.code(report_text, language="text")
            
            # --- 2. グラフィカルUI ---
            
            # 2.1 Core Numbers & Themes (統合セクション)
            st.markdown('<div class="section-header">🧩 [ Core Numbers & Themes ]</div>', unsafe_allow_html=True)
            
            # 1段目 (Core Numbers)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Birth Number", res["BirthNum"])
            c2.metric("Destiny Number", res["DestinyNum"])
            c3.metric("Soul Number", res["SoulNum"])
            c4.metric("Personality Number", res["PersoNum"])
            c5.metric("Realization Number", res["RealizNum"])
            
            st.write("") # 上下段の間のわずかな余白
            
            # 2段目 (Themes)
            c6, c7, c8, c9 = st.columns(4)
            c6.metric("Stage Number", res["StageNum"])
            c7.metric("Challenge Number", res["ChallNum"])
            c8.metric("New Strengths", res["Strengths"])
            c9.metric("Sub Theme", res["SubTheme"])

            # 2.3 Turning Point Ages
            st.markdown('<div class="section-header">⏳ [ Turning Point Ages ]</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("1st Turning Point", f"{res['TP'][0]} yrs")
            c2.metric("2nd Turning Point (Main)", f"{res['TP'][1]} yrs")
            c3.metric("3rd Turning Point", f"{res['TP'][2]} yrs")

            # 2.4 Life Cycle Stages
            st.markdown('<div class="section-header">📅 [ Life Cycle Stages ]</div>', unsafe_allow_html=True)
            df_stages = pd.DataFrame(res["Stages"])
            df_stages.columns = ["Term", "Age Range", "Milestone", "Rout", "Hardships"]
            
            styled_stages = df_stages.style.set_properties(**{'text-align': 'center'}) \
                .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]) \
                .hide(axis="index")
            st.table(styled_stages)
            
            # 2.5 Nine Box (Magic Array)
            st.markdown('<div class="section-header">🔮 [ Nine Box (Magic Array) ]</div>', unsafe_allow_html=True)
            
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
                sum_lines_data = [
                    {"name": "3-6-9", "val": c[3]+c[6]+c[9]},
                    {"name": "2-5-8", "val": c[2]+c[5]+c[8]},
                    {"name": "1-4-7", "val": c[1]+c[4]+c[7]},
                    {"name": "1-2-3", "val": c[1]+c[2]+c[3]},
                    {"name": "4-5-6", "val": c[4]+c[5]+c[6]},
                    {"name": "7-8-9", "val": c[7]+c[8]+c[9]},
                    {"name": "3-5-7", "val": c[3]+c[5]+c[7]},
                    {"name": "1-5-9", "val": c[1]+c[5]+c[9]}
                ]
                max_val = max([s["val"] for s in sum_lines_data]) if sum_lines_data else 1
                max_val = max_val if max_val > 0 else 1 
                
                sum_html = "<table style='width:100%; border-collapse: collapse; margin-top: 10px; color: inherit;'>"
                sum_html += "<tr style='border-bottom: 2px solid var(--border-color);'><th style='padding:8px; text-align:center;'>Sum Lines</th><th style='padding:8px; text-align:center;'>Sum</th><th style='padding:8px; width:50%;'></th></tr>"
                for s in sum_lines_data:
                    bar_w = int((s["val"] / max_val) * 100)
                    bar = f"<div style='width:{bar_w}%; background-color:#4a90e2; height:12px; border-radius:3px;'></div>" if s["val"] > 0 else ""
                    sum_html += f"<tr><td style='padding:8px; border-bottom:1px solid var(--border-color); text-align:center;'>{s['name']}</td><td style='padding:8px; border-bottom:1px solid var(--border-color); text-align:center; font-weight:bold;'>{s['val']}</td><td style='padding:8px; border-bottom:1px solid var(--border-color);'>{bar}</td></tr>"
                sum_html += "</table>"
                st.markdown(sum_html, unsafe_allow_html=True)

            # 2.6 Yearly Cycle Table 
            st.markdown('<div class="section-header">🌊 [ Yearly Cycle Table (Age 0 - 80) ]</div>', unsafe_allow_html=True)
            cycle_data = []
            cycle_keywords = {
                1: "Beginning", 2: "Alignment", 3: "Creation", 4: "Stability", 5: "Movement",
                6: "Love", 7: "Refrection", 8: "Enrich", 9: "Completion"
            }
            for age in range(81):
                y = res["BirthYear"] + age
                cyc = chart._get_personal_year(y, res["BirthMonth"], res["BirthDay"])
                theme = cycle_keywords.get(cyc, "")
                cycle_data.append({"Age": age, "Year": y, "Cycle": cyc, "Theme": theme})
            
            df_cycles = pd.DataFrame(cycle_data)

            def color_cycle(val):
                colors = {
                    1: '#ffe5e5', 2: '#fff2e5', 3: '#ffffe5', 
                    4: '#e5ffe5', 5: '#e5ffff', 6: '#e5f2ff', 
                    7: '#e5e5ff', 8: '#f2e5ff', 9: '#ffe5f2'
                }
                bg_color = colors.get(val, '')
                return f'background-color: {bg_color}; color: #000000;' if bg_color else ''

            col_a, col_b, col_c = st.columns(3)
            
            def style_cycles(df):
                return df.style.map(color_cycle, subset=['Cycle']) \
                               .set_properties(**{'text-align': 'center'}) \
                               .set_table_styles([dict(selector='th', props=[('text-align', 'center')])]) \
                               .hide(axis="index")

            with col_a:
                st.table(style_cycles(df_cycles.iloc[0:27]))
            with col_b:
                st.table(style_cycles(df_cycles.iloc[27:54]))
            with col_c:
                st.table(style_cycles(df_cycles.iloc[54:81]))

            # --- 3. グラフィカルPDF ---
            st.markdown('<div class="section-header">📥 [ Export Report ]</div>', unsafe_allow_html=True)
            if HAS_FPDF:
                pdf_filename = f"{name_in.replace(' ', '_')}_Graphical.pdf"
                chart.export_graphical_pdf(pdf_filename)
                
                with open(pdf_filename, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Download Full Graphical PDF",
                        data=pdf_file,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                os.remove(pdf_filename)
            else:
                st.warning("PDF export is unavailable. Please install 'fpdf'.")
    else:
        st.error("Error: Birthday must be exactly 8 digits (YYYYMMDD).")