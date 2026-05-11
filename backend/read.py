import pandas as pd

# ================= READ SMALL SAMPLE =================

patents = pd.read_csv(
    "g_patent.tsv",
    sep="\t",
    low_memory=False,
    nrows=5
)

abstracts = pd.read_csv(
    "g_patent_abstract.tsv",
    sep="\t",
    low_memory=False,
    nrows=5
)

inventors = pd.read_csv(
    "g_inventor_disambiguated.tsv",
    sep="\t",
    low_memory=False,
    nrows=5
)

relationships = pd.read_csv(
    "g_persistent_inventor.tsv",
    sep="\t",
    low_memory=False,
    nrows=5
)

assignees = pd.read_csv(
    "g_assignee_disambiguated.tsv/g_assignee_disambiguated.tsv",
    sep="\t",
    low_memory=False,
    nrows=5
)

locations = pd.read_csv(
    "g_location_disambiguated.tsv/g_location_disambiguated.tsv",
    sep="\t",
    low_memory=False,
    nrows=5
)

# ================= PRINT =================

print("\nPATENTS\n")
print(patents)

print("\nABSTRACTS\n")
print(abstracts)

print("\nINVENTORS\n")
print(inventors)

print("\nRELATIONSHIPS\n")
print(relationships)

print("\nASSIGNEES\n")
print(assignees)

print("\nLOCATIONS\n")
print(locations)