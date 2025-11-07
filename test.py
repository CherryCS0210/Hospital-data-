import pandas as pd, numpy as np

# ---- base data ----
cols = ["Name","Age","Height_cm","Weight_kg","Condition"]
df = pd.DataFrame([
    ["Kapil",105,176,30,"Kidney fail"],
    ["Arnab",156,149,90,"High blood pressure"],
    ["Lily", 92,168,68,"Lung infection"],
], columns=cols)

def _recalc(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["BMI"] = (d["Weight_kg"] / (d["Height_cm"] / 100) ** 2).round(1)
    d["High_risk"] = np.where((d["BMI"] >= 30) | (d["Condition"].str.casefold() == "high blood pressure"), "Yes", "No")
    return d

def add_patient(d: pd.DataFrame, name, age, h_cm, w_kg, cond) -> pd.DataFrame:
    d = pd.concat([d, pd.DataFrame([[name, age, h_cm, w_kg, cond]], columns=cols)], ignore_index=True)
    d.insert(0, "Patient_ID", range(1, len(d) + 1)) if "Patient_ID" not in d else d.__setitem__("Patient_ID", range(1, len(d) + 1))
    return _recalc(d)

# ---- init + sample extra row ----
df = _recalc(df)
df.insert(0, "Patient_ID", range(1, len(df) + 1))
df = add_patient(df, "Kapil", 105, 176, 30, "Kidney fail")

# ---- save safely (Excel optional) ----
df.to_csv("patients.csv", index=False)
try:
    df.to_excel("patients.xlsx", index=False)  # requires 'openpyxl'
except Exception as e:
    print(f"[Note] Excel save skipped: {e}")

# ---- search menu ----
def search_menu(d: pd.DataFrame):
    print("\nSearch Patient By:\n1. Exact Name\n2. Partial Name\n3. Patient ID")
    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice == "1":
        name = input("Enter Exact Name: ").strip()
        result = d[d["Name"].str.casefold() == name.casefold()]

    elif choice == "2":
        part = input("Enter part of name: ").strip()
        # regex=False avoids errors with characters like [ ] ( ) . * etc.
        result = d[d["Name"].str.contains(part, case=False, regex=False, na=False)]

    elif choice == "3":
        pid = input("Enter Patient ID: ").strip()
        result = d[d["Patient_ID"] == int(pid)] if pid.isdigit() else pd.DataFrame()

    else:
        print("\nInvalid option!")
        result = pd.DataFrame()

    if result.empty:
        print("\nNo matching patient found!")
    else:
        print("\nPatient Details:\n")
        print(result.to_string(index=False))

# Run the search once (or wrap in a loop if you want)
search_menu(df)
