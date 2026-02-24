import json

with open('data/chapters.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

ch3 = data[2]  # Capitol 3
ch4 = data[3]  # Capitol 4

print(f"Capitol 3 ({ch3['title']}): {len(ch3.get('lessons', []))} lectii")
print(f"Capitol 4 ({ch4['title']}): {len(ch4.get('lessons', []))} lectii")

if len(ch3['lessons']) > 10:
    print("\n✓ Capitol 3 REPARAT!")
else:
    print("\n✗ Capitol 3 are inca probleme")

if len(ch4['lessons']) > 10:
    print("✓ Capitol 4 REPARAT!")
else:
    print("✗ Capitol 4 are inca probleme")

# Verificare JSON valid
print(f"\n✓ JSON valid: {len(data)} capitole totale")
