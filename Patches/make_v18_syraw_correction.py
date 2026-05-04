from pathlib import Path

src = Path("rytm_hybrid_randomizer_v17.py")
dst = Path("rytm_hybrid_randomizer_v18.py")

if not src.exists():
    raise SystemExit("Could not find rytm_hybrid_randomizer_v17.py")

text = src.read_text()

text = text.replace(
    'print("\\nRYTM HYBRID RANDOMIZER V1.7 - BD + SY RAW LFO\\n")',
    'print("\\nRYTM HYBRID RANDOMIZER V1.8 - CORRECTED SY RAW BALANCE / NOISE\\n")'
)

# Correct SY Raw mapping:
# Earlier we interpreted CC19 as Balance and CC23 as Noise.
# Your hands-on capture confirms the opposite:
# CC19 = Noise Level
# CC23 = Balance

text = text.replace('"SRC Balance"', '"__TEMP_SY_RAW_BALANCE__"')
text = text.replace('"SRC Noise Level"', '"SRC Balance"')
text = text.replace('"__TEMP_SY_RAW_BALANCE__"', '"SRC Noise Level"')

dst.write_text(text)

print("Created rytm_hybrid_randomizer_v18.py")
print("Corrected SY Raw mapping:")
print("  CC19 = SRC Noise Level")
print("  CC23 = SRC Balance")
print("Run it with: python .\\rytm_hybrid_randomizer_v18.py")
