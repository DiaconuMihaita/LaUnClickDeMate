import json

with open('data/chapters.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total capitole: {len(data)}\n")
for i, ch in enumerate(data, 1):
    lessons_count = len(ch.get('lessons', []))
    examples_count = len(ch.get('examples', []))
    exercises_count = len(ch.get('exercises', []))
    
    status = "✅" if lessons_count > 3 else "❌"
    print(f"{status} {i}. {ch['title']}")
    print(f"   Lecții: {lessons_count}, Exemple: {examples_count}, Exerciții: {exercises_count}")
    
    if lessons_count <= 3:
        print(f"   ⚠️  CAPITOL CU PROBLEME!")
    print()
