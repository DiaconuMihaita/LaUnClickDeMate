import json

# Definirea datelor într-o structură Python pentru a evita erorile de sintaxă string
chapters = [
    {
        "id": "intro_scriere_citire",
        "title": "1. Scrierea și citirea numerelor naturale",
        "icon": "🔢",
        "keywords": ["scriere", "citire", "sistem zecimal", "cifre", "infinit", "pozitionala", "clase", "miliarde", "milioane", "mii", "unitati", "ab", "abc", "zecimal", "numere", "numar", "scrie", "citeste", "cifra", "pozitie", "ordin", "descompunere"],
        "lessons": [
            "Scrierea: Așa cum un text este alcătuit din litere și cuvinte, limbajul matematic este alcătuit din cifre și numere.",
            "! Cifrele în sistemul de numerație zecimal sunt: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9",
            "Numărul numerelor naturale este infinit și totuși trebuie să găsim o metodă să le scriem cu cele zece cifre.",
            "Sistemul folosit de noi se numește sistemul de numerație zecimal. Folosim această denumire pentru că: - zece unități formează un zece - zece zeci formează o sută - zece sute formează o mie ș.a.m.d.",
            "! Fiecare număr se scrie ca o succesiune de cifre, care se pot repeta și prima cifră a unui număr (mai mult de două cifre) nu poate fi 0.",
            "! Valoarea fiecărei cifră depinde de poziția ei ocupată în număr, de acea această scriere se numește scriere pozițională.",
            "Citirea: Pentru a citi un număr natural, separăm cifrele sale în grupe de câte trei, plecând de la dreapta spre stânga. Grupele obținute se numesc clase. Fiecare clasă este alcătuită din unități, zeci și sute.",
            "Tabelul Claselor (de la stânga la dreapta): <br>1. Clasa miliardelor (sute, zeci, unități)<br>2. Clasa milioanelor (sute, zeci, unități)<br>3. Clasa miilor (sute, zeci, unități)<br>4. Clasa unităților (sute, zeci, unități)",
            "! În matematică orice număr (cifră) necunoscut se notează cu o literă: a, b, c, x, y, z",
            "! Un număr de două cifre: 𝑎𝑏, unde a ocupă locul zecilor (a≠0) și b a unităților. Deci 𝑎𝑏 = 𝑎∙10 + 𝑏∙1.",
            "! Un număr de trei cifre: 𝑎𝑏𝑐, unde a ocupă locul sutelor (a≠0), b a zecilor și c a unităților. Deci 𝑎𝑏𝑐 = 𝑎∙100 + 𝑏∙10 + 𝑐∙1."
        ],
        "examples": [
            "Ex. 1435 = 5∙1 + 3∙10 + 4∙100 + 1∙1000. Deci 5 arată numărul unităților, 3 al zecilor, 4 al sutelor și 1 al miilor.",
            "Ex. Numărul 234 567 890 123.",
            "În tabel: Miliarde (2,3,4), Milioane (5,6,7), Mii (8,9,0), Unități (1,2,3).",
            "Citit: două sute treizeci și patru miliarde cinci sute șaizeci și șapte milioane opt sute nouăzeci mii o sută douăzeci și trei."
        ],
        "exercises": [
            {"question": "Scrie sub formă de sumă pozițională numărul 7894.", "answer": "4+90+800+7000"},
            {"question": "Câte clase are un număr de 9 cifre?", "answer": "3"},
            {"question": "Care este cifra zecilor în numărul 4583?", "answer": "8"}
        ],
        "fun_facts": [
            "🌍 Cele mai vechi numere scrise au fost descoperite în Mesopotamia, pe tăblițe de lut, acum peste 5000 de ani!",
            "🔢 Sistemul zecimal a fost inventat în India antică și apoi răspândit de arabii care l-au adus în Europa.",
            "💡 Cifra 0 a fost inventată în India în jurul anului 500. Fără ea, nu am putea scrie numere precum 10, 100 sau 1000!"
        ],
        "dictionary": {
            "numere naturale": "Numerele naturale sunt numere întregi, pozitive, incluzând zero (0), utilizate pentru numărare și ordonare. Mulțimea lor este notată cu N. Acestea sunt ordonate, fiecare număr având un succesor mai mare, și formează baza sistemului zecimal de numerație.",
            "cifra": "0-9, simbolurile de bază.",
            "pozițional": "Valoarea cifrei depinde de locul ei.",
            "clasa": "Grupă de 3 cifre.",
            "zecimal": "Sistem bazat pe numărul 10."
        }
    },
    {
        "id": "sir_axa_naturale",
        "title": "2. Șirul și axa numerelor naturale",
        "icon": "📍",
        "keywords": ["sir", "axa", "consecutive", "predecesor", "succesor", "nenule", "pare", "impare", "sir numere", "dreapta numerica", "coordonata", "punct", "origine", "termen"],
        "lessons": [
            "Șirul numerelor naturale: 0, 1, 2, 3, 4, ... . Șirul este infinit, iar numerele se numesc termenii șirului și au un loc bine fixat.",
            "Șirul numerelor naturale nenule (diferite de zero): 1, 2, 3, 4, ...",
            "Șirul numerelor naturale pare: 0, 2, 4, 6, ... . Forma generală: 2∙n.",
            "Șirul numerelor naturale impare: 1, 3, 5, 7, ... . Forma generală: 2∙n+1.",
            "Fie n un număr natural: n-1 se numește predecesorul lui n; n+1 se numește succesorul lui n; n-1, n, n+1 se numesc numere naturale consecutive.",
            "Axa numerelor: este o dreaptă cu un punct O (origine), un sens pozitiv (săgeată) și o unitate de măsură.",
            "O(0) se citește 'punctul O de coordonată zero'. Coordonata unui punct este egală cu numărul unităților de măsură de la origine până la punct."
        ],
        "examples": [
            "1) În șirul natural pe locul 10 se află numărul 9 (10-1=9).",
            "2) Pe locul 17 în șirul pare se află numărul 32 (17·2-2=32).",
            "3) Numărul 173 se află pe locul 87 în șirul impare (174:2=87).",
            "4) Numărul 134 se află pe locul 68 în șirul pare (134:2+1=68).",
            "5) Pe locul 100 în șirul impare se află numărul 199 (100·2-1=199).",
            "10) Predecesorul celui de-al 24-lea termen nenul: al 24-lea e 24, predecesorul e 23."
        ],
        "exercises": [
            {"question": "Află coordonata punctului aflat la 7 unități de origine.", "answer": "7"},
            {"question": "Scrie 3 numere naturale consecutive din care unul este 10.", "answer": "9, 10, 11"},
            {"question": "Care este succesorul numărului 99?", "answer": "100"}
        ],
        "fun_facts": [
            "📍 Ideea de 'axă a numerelor' a fost introdusă de matematicianul John Wallis în 1685!",
            "🔄 Numerele pare și impare se alternează mereu: par, impar, par, impar... la infinit!",
            "🐢 Filosoful grec Zenon credea că mișcarea e imposibilă din cauza numărului infinit de puncte de pe o dreaptă!"
        ],
        "dictionary": {
            "numere naturale": "Numerele naturale sunt numere întregi, pozitive, incluzând zero (0), utilizate pentru numărare și ordonare.",
            "termen": "Fiecare număr din șir.",
            "nenule": "Diferite de zero.",
            "coordonata": "Numărul corespunzător punctului pe axă.",
            "origine": "Punctul zero de pe axă."
        }
    },
    {
        "id": "comparare_ordonare",
        "title": "3. Compararea și ordonarea numerelor naturale",
        "icon": "⚖️",
        "keywords": ["comparare", "ordonare", "crescator", "descrescator", "mai mic", "mai mare", "egal", "semne", "ordine", "compara", "ordoneaza", "cifra cu cifra"],
        "lessons": [
            "Semne folosite: < (mai mic), > (mai mare), = (egal).",
            "Regula 1: Dintre două numere care nu au același număr de cifre, este mai mare cel cu mai multe cifre. Ex: 1256 < 34580.",
            "Regula 2: Dacă au număr egal de cifre, se compară cifră cu cifră de la stânga la dreapta. Este mai mare numărul cu prima cifră diferită mai mare. Ex: 3675 > 3629."
        ],
        "examples": [
            "1256 < 34580 (4 cifre vs 5 cifre).",
            "3675 > 3629 (la zeci 7 > 2)."
        ],
        "exercises": [
            {"question": "Ordonează descrescător: 12, 120, 125, 1205.", "answer": "1205, 125, 120, 12"},
            {"question": "Găsește cifrele x pentru care 2x5 < 235.", "answer": "0, 1, 2"},
            {"question": "Pune semnul corect: 7892 ___ 7829", "answer": ">"}
        ],
        "fun_facts": [
            "⚖️ Semnele < și > au fost inventate de matematicianul englez Thomas Harriot în 1631!",
            "📏 Calculatoarele compară miliarde de numere pe secundă — dar folosesc aceleași reguli ca tine!"
        ]
    },
    {
        "id": "aproximari_rotunjiri",
        "title": "4. Aproximări și Rotunjiri",
        "icon": "🎯",
        "keywords": ["aproximare", "lipsa", "adaos", "rotunjire", "zeci", "sute", "mii", "rotunjeste", "aproximeaza", "rotund", "estimare"],
        "lessons": [
            "Aproximarea: Când nu știm valoarea reală, folosim o valoare apropiată.",
            "Relație: aproximarea prin lipsă < numărul natural < aproximarea prin adaos.",
            "Rotunjirea: Este aproximarea cea mai apropiată grafic. Regula: dacă cifra următoare e 0,1,2,3,4 -> lipsă; dacă e 5,6,7,8,9 -> adaos."
        ],
        "examples": [
            "Rotunjiri 15264: la zeci (15260), la sute (15300), la mii (15000).",
            "Tabel 3187: Lipsă zeci (3180), sute (3100), mii (3000). Adaos zeci (3190), sute (3200), mii (4000)."
        ],
        "exercises": [
            {"question": "Rotunjește 4567 la sute.", "answer": "4600"},
            {"question": "Aproximează prin lipsă la mii numărul 78047.", "answer": "78000"},
            {"question": "Rotunjește 3450 la mii.", "answer": "3000"}
        ],
        "fun_facts": [
            "🎯 Rotunjirea este folosită zilnic! De exemplu, când spui 'am avut 98 de puncte', adesea rotunjești la 100.",
            "🚀 NASA folosește rotunjiri complexe pentru a calcula traiectoriile rachetelor în spațiu!"
        ]
    },
    {
        "id": "adunarea_naturale",
        "title": "5. Adunarea numerelor naturale",
        "icon": "➕",
        "keywords": ["adunare", "suma", "termeni", "comutativa", "asociativa", "element neutru", "Gauss", "plus", "adun", "aduna", "calcul adunare", "suma gauss"],
        "lessons": [
            "Definiție: a + b = s (termeni -> sumă).",
            "Proprietăți: 1. Comutativă (a+b=b+a). 2. Asociativă ((a+b)+c=a+(b+c)). 3. 0 este element neutru (a+0=a).",
            "Sume Gauss: 1 + 2 + 3 + ... + n = n ∙ (n + 1) : 2 (pentru n > 2)."
        ],
        "exercises": [
            {"question": "Calculează suma 1+2+...+100.", "answer": "5050"},
            {"question": "Dacă x+y=20 și x+2y=39, cât este y?", "answer": "19"},
            {"question": "Calculează: 347 + 653.", "answer": "1000"}
        ],
        "fun_facts": [
            "🧒 Carl Friedrich Gauss a descoperit formula sumei 1+2+...+n la doar 9 ani!",
            "➕ Semnul '+' a fost folosit prima dată de matematicianul Johannes Widmann în 1489."
        ]
    },
    {
        "id": "scaderea_naturale",
        "title": "6. Scăderea numerelor naturale",
        "icon": "➖",
        "keywords": ["scadere", "diferenta", "descazut", "scazator", "proba", "inegalitati", "minus", "scad", "scade", "rest scadere"],
        "lessons": [
            "Definiție: a - b = d (descăzut - scăzător = diferență). a ≥ b. d + b = a.",
            "Metodă: Se scad unitățile de același ordin. Dacă nu sunt suficiente, se împrumută de la ordinul imediat superior."
        ],
        "exercises": [
            {"question": "Efectuează proba pentru 890 - 456.", "answer": "434"},
            {"question": "Diferența a două numere este 45. Scăzătorul este 12. Care e descăzutul?", "answer": "57"},
            {"question": "Calculează: 10000 - 4567.", "answer": "5433"}
        ],
        "fun_facts": [
            "➖ Semnul minus '-' a fost folosit prima dată tot de Johannes Widmann în 1489.",
            "🧮 În Egiptul antic, scăderea era considerată mai grea decât adunarea."
        ]
    },
    {
        "id": "inmultirea_naturale",
        "title": "7. Înmultirea numerelor naturale",
        "icon": "✖️",
        "keywords": ["inmultire", "produs", "factori", "distributivitate", "element neutru", "ori", "inmultesc", "multiplicare", "tabla inmultirii", "inmultit"],
        "lessons": [
            "Definiție: a ∙ b = c (factor ∙ factor = produs).",
            "Proprietăți: 1. Comutativă (ab=ba). 2. Asociativă. 3. 1 este element neutru (a*1=a). 4. Distributivitate: a∙(b+c) = ab+ac."
        ],
        "exercises": [
            {"question": "Calculează 25∙4∙12 folosind asociativitatea.", "answer": "1200"},
            {"question": "Efectuează 15∙(10+2).", "answer": "180"},
            {"question": "Un fermier are 8 rânduri cu câte 15 pomi. Câți pomi are în total?", "answer": "120"}
        ],
        "fun_facts": [
            "✖️ Semnul '∙' pentru înmulțire a fost folosit prima dată de Leibniz.",
            "🧮 Tabla înmulțirii era cunoscută de babilonieni acum 4000 de ani!"
        ]
    },
    {
        "id": "impartirea_naturale",
        "title": "8. Împărțirea numerelor naturale",
        "icon": "➗",
        "keywords": ["impartire", "cat", "rest", "deimpartit", "impartitor", "exacta", "teorema restului", "divide", "impart", "impartire cu rest", "impartire exacta"],
        "lessons": [
            "Împărțirea exactă: a : b = c (b≠0) dacă a = b ∙ c.",
            "! Împărțirea la 0 nu are sens!",
            "Teorema împărțirii cu rest: a = b ∙ c + r și r < b. c și r sunt unice."
        ],
        "exercises": [
            {"question": "Află câtul și restul pentru 157 : 12.", "answer": "13 rest 1"},
            {"question": "Care sunt resturile posibile la împărțirea cu 9?", "answer": "0, 1, 2, 3, 4, 5, 6, 7, 8"},
            {"question": "Câte grupe de câte 6 copii se pot forma din 50 de copii?", "answer": "8"}
        ],
        "fun_facts": [
            "➗ Semnul ÷ a fost inventat de suedezul Johann Rahn în 1659!",
            "🤯 Împărțirea la zero poate 'sparge' orice calculator!"
        ]
    },
    {
        "id": "factorul_comun",
        "title": "9. Factorul comun",
        "icon": "🔗",
        "keywords": ["factor comun", "ab+ac", "simplificare", "scoatere factor", "factor", "comun", "paranteza"],
        "lessons": [
            "Definiție: Dacă un factor apare în ambii termeni ai unei sume/diferențe, el este factor comun.",
            "Formule: ab + ac = a ∙ (b + c) și ab - ac = a ∙ (b - c)."
        ],
        "exercises": [
            {"question": "Scoate factor comun în: 12∙3 + 12∙7.", "answer": "120"},
            {"question": "Calculează rapid: 15∙99 + 15.", "answer": "1500"},
            {"question": "Calculează: 33∙17 + 33∙83.", "answer": "3300"}
        ],
        "fun_facts": [
            "🔗 Factorizarea este baza criptografiei moderne.",
            "🧩 Scoaterea factorului comun face calcule grele să devină foarte ușoare!"
        ]
    },
    {
        "id": "puteri_naturale",
        "title": "10. Ridicarea la putere",
        "icon": "⚡",
        "keywords": ["putere", "baza", "exponent", "patrat perfect", "cub", "ridicare", "patrat", "puterea", "la putere", "exponentul"],
        "lessons": [
            "Definiție: a·a·...·a (de n ori) = a^n. a - baza, n - exponent.",
            "Pătrat perfect: a^2. Cubul: a^3.",
            "Convenții: a^1=a; a^0=1 (a≠0)."
        ],
        "exercises": [
            {"question": "Scrie 81 ca putere a lui 3.", "answer": "3^4"},
            {"question": "Este 125 pătrat perfect sau cub?", "answer": "cub"},
            {"question": "Calculează 2^5.", "answer": "32"}
        ],
        "fun_facts": [
            "⚡ Numerele ridicate la putere cresc ENORM de repede!",
            "♟️ Legenda spune că inventatorul șahului a cerut regelui 2^63 boabe de grâu."
        ]
    },
    {
        "id": "reguli_calcul_puteri",
        "title": "11. Reguli de calcul cu puteri",
        "icon": "📜",
        "keywords": ["reguli puteri", "am an", "am:an", "puterea unei puteri", "inmultire puteri", "impartire puteri", "aceeasi baza"],
        "lessons": [
            "Regula 1: a^m ∙ a^n = a^(m+n).",
            "Regula 2: a^m : a^n = a^(m-n).",
            "Regula 3: (a^m)^n = a^(m∙n)."
        ],
        "exercises": [
            {"question": "Adu la aceeași bază: 2^5 ∙ 4^2.", "answer": "2^9"},
            {"question": "Calculează: 10^5 : 10^3.", "answer": "100"},
            {"question": "Simplifică: (5^3)^2.", "answer": "5^6"}
        ],
        "fun_facts": [
            "📜 Regulile puterilor au fost formalizate de matematianul arab Al-Khwarizmi.",
            "💾 Calculatoarele folosesc puterile lui 2: 1 KB = 1024 bytes."
        ]
    },
    {
        "id": "compararea_puterilor",
        "title": "12. Compararea puterilor",
        "icon": "↔️",
        "keywords": ["comparare puteri", "aceeasi baza", "acelasi exponent", "compara puteri", "mai mare putere", "mai mica putere"],
        "lessons": [
            "Caz 1: Aceeași bază: a^n < a^m dacă n < m (a≠1).",
            "Caz 2: Același exponent: a^n < b^n dacă a < b (n≠0)."
        ],
        "exercises": [
            {"question": "Compară 5^100 cu 5^101.", "answer": "5^100 < 5^101"},
            {"question": "Compară 2^60 cu 3^40 (adu la exponent 20).", "answer": "2^60 < 3^40"}
        ],
        "fun_facts": [
            "↔️ Compararea puterilor mari este esențială în criptografie.",
            "🔬 Oamenii de știință compară puteri uriașe pentru a estima distanțe în univers!"
        ]
    },
    {
        "id": "ordine_operatii",
        "title": "13. Ordinea operațiilor și parantezele",
        "icon": "🔢",
        "keywords": ["ordine", "paranteze", "grad 1", "grad 2", "grad 3", "ordinea operatiilor", "prioritate", "parantezerotunde", "paranteze patrate", "acolade"],
        "lessons": [
            "Regula 1: Numai operații de același ordin -> de la stânga la dreapta.",
            "Regula 2: Ordine: I. Putere. II. Înmultire/Impărțire. III. Adunare/Scădere.",
            "Regula 3: Paranteze: întai (), apoi [], apoi {}."
        ],
        "exercises": [
            {"question": "Calculează: 2 + 2 ∙ 2.", "answer": "6"},
            {"question": "Rezolvă: 10 - [ 2 ∙ ( 3 + 1 ) ].", "answer": "2"},
            {"question": "Calculează: (5+3) ∙ 2 - 4.", "answer": "12"}
        ],
        "fun_facts": [
            "🔢 Regula PEMDAS este aceeași în toată lumea!",
            "🤖 Calculatoarele respectă aceeași ordine a operațiilor pe care o înveți tu!"
        ]
    },
    {
        "id": "baze_aritmetica",
        "title": "14. Baze de numerație",
        "icon": "⚖️",
        "keywords": ["baza 10", "baza 2", "zecimal", "binar", "conversie", "baze numeratie", "sistem binar", "calculator binar", "transforma", "conversie binar"],
        "lessons": [
            "Baza 10: Sistem zecimal. 135(10) = 1∙10^2+3∙10+5.",
            "Baza 2: Sistem binar (cifre 0 și 1).",
            "Conversie 10 în 2: Prin împărțiri succesive la 2."
        ],
        "exercises": [
            {"question": "Transformă 50 în baza 2.", "answer": "110010"},
            {"question": "Ce număr zecimal este 111(2)?", "answer": "7"},
            {"question": "Transformă 10 în binar.", "answer": "1010"}
        ],
        "fun_facts": [
            "💻 Toate calculatoarele 'gândesc' în baza 2!",
            "🎵 Muzica pe telefon este stocată ca o secvență de 0 și 1!"
        ]
    },
    {
        "id": "media_aritmetica",
        "title": "15. Media Aritmetică",
        "icon": "📊",
        "keywords": ["media", "ma", "note", "medie", "media aritmetica", "media notelor", "medie aritmetica"],
        "lessons": [
            "Pentru 2 numere: ma = (a + b) : 2.",
            "Pentru n numere: ma = (Suma elementelor) : n.",
            "! Media nu este mereu număr natural!"
        ],
        "exercises": [
            {"question": "Calculează media aritmetică a numerelor 4, 8, 12.", "answer": "8"},
            {"question": "Media a două numere este 15. Un număr este 10. Care este celălalt?", "answer": "20"},
            {"question": "Care este media aritmetică a numerelor 3, 5, 7, 9?", "answer": "6"}
        ],
        "fun_facts": [
            "📊 Media aritmetică este folosită la note în școală, temperaturi și statistici!",
            "⚽ Media golurilor pe meci este esențială în fotbal!"
        ]
    },
    {
        "id": "metode_aritmetice_1",
        "title": "16. Metoda reducerii la unitate",
        "icon": "🧩",
        "keywords": ["reducere unitate", "1 kg", "dependeta", "metoda", "reducere", "unitate", "proportie", "regula de trei"],
        "lessons": [
            "Algoritm: Aflăm mărimea pentru unitate (1 obiect/1 kg) pentru a găsi rezultatul cerut.",
            "Tip I: Ambele cresc/scad la fel. Tip II: Una crește, alta scade."
        ],
        "exercises": [
            {"question": "5 caiete costă 10 lei. Cât costă 8 caiete?", "answer": "16"},
            {"question": "Un tren parcurge 120 km în 2 ore. Cât parcurge în 5 ore?", "answer": "300"},
            {"question": "3 kg de mere costă 12 lei. Cât costă 7 kg?", "answer": "28"}
        ],
        "fun_facts": [
            "🧩 Această metodă este folosită zilnic la cumpărături și la gătit!",
            "🏪 Supermarket-urile afișează prețul pe kilogram folosind această metodă."
        ]
    },
    {
        "id": "metode_aritmetice_2",
        "title": "17. Metoda Comparației",
        "icon": "⚖️",
        "keywords": ["comparatie", "eliminare", "inlocuire", "ecuatii", "sistem ecuatii", "metoda comparatiei", "necunoscuta"],
        "lessons": [
            "Esență: Comparăm două situații diferite pentru a elimina o necunoscută.",
            "Situații: 1. Eliminare prin scădere. 2. Eliminare prin înlocuire."
        ],
        "exercises": [
            {"question": "2 mere + 3 pere = 13 lei; 2 mere + 5 pere = 19 lei. Află prețul pentru 1 măr.", "answer": "2"},
            {"question": "3 pixuri + 2 creioane = 16 lei; 3 pixuri + 4 creioane = 22 lei. Cât costă un creion?", "answer": "3"}
        ],
        "fun_facts": [
            "⚖️ Metoda comparației este baza algebrei.",
            "🔍 Detectivii folosesc aceeași logică!"
        ]
    },
    {
        "id": "metode_aritmetice_3",
        "title": "18. Metoda Mersului Invers",
        "icon": "🔙",
        "keywords": ["mers invers", "operatii inverse", "Antonia", "invers", "de la sfarsit", "mersul inapoi", "operatia inversa"],
        "lessons": [
            "Concept: Rezolvăm problema de la sfârșit către început folosind operații inverse.",
            "Aplicații: Probleme cu 'un număr la care m-am gândit'."
        ],
        "exercises": [
            {"question": "Anabela: (n:4)+7=18. Află n.", "answer": "44"},
            {"question": "Află x: [(x : 4 + 5) : 6 + 10] : 10 + 3 = 13.", "answer": "220"},
            {"question": "M-am gândit la un număr, l-am dublat și am adăugat 6. Am obținut 20. La ce număr m-am gândit?", "answer": "7"}
        ],
        "fun_facts": [
            "🔙 Mersul invers se numește 'backtracking' în programare.",
            "🕵️ Detectivii reconstituie evenimentele de la final spre început!"
        ]
    },
    {
        "id": "metode_aritmetice_4",
        "title": "19. Metoda Falsei Ipoteze",
        "icon": "❓",
        "keywords": ["falsa ipoteza", "presupunere", "eroare", "iepuri", "gaini", "presupunem", "ipoteza", "falsă ipoteză"],
        "lessons": [
            "Algoritm: Presupunem că toate elementele sunt de un singur fel. Calculăm eroarea față de realitate și corectăm diferența.",
            "Exemplu clasic: Găini și Iepuri."
        ],
        "exercises": [
            {"question": "În curte sunt 20 de oi și gâște, având 50 de picioare. Câte oi sunt?", "answer": "5"},
            {"question": "30 de animale (găini și iepuri) au 80 de picioare. Câte găini sunt?", "answer": "20"},
            {"question": "În parcare sunt 15 biciclete și mașini cu 46 de roți. Câte mașini sunt?", "answer": "8"}
        ],
        "fun_facts": [
            "❓ Problema 'găinilor și iepurilor' are peste 1500 de ani!",
            "🎭 'Falsa ipoteză' este ca un experiment de gândire."
        ]
    },
    {
        "id": "divizibilitate",
        "title": "20. Divizibilitatea",
        "icon": "📐",
        "keywords": ["divizibil", "divizor", "multiplu", "impropriu", "propriu", "divide", "se imparte", "se divide", "multipli"],
        "lessons": [
            "Definiție: a ⋮ b dacă a = b ∙ c.",
            "Divizori improprii: 1 și el însuși. Divizori proprii: Toți ceilalți.",
            "Numărul 0 se divide cu orice număr natural nenul."
        ],
        "exercises": [
            {"question": "Scrie toți divizorii lui 12.", "answer": "1, 2, 3, 4, 6, 12"},
            {"question": "Care este cel mai mic multiplu nenul al lui 5?", "answer": "5"},
            {"question": "Este 36 multiplu al lui 9?", "answer": "da"}
        ],
        "fun_facts": [
            "📐 Divizibilitatea protejează tranzacțiile tale bancare!",
            "🔢 Numărul 1 este divizor al TUTUROR numerelor naturale!"
        ]
    },
    {
        "id": "criterii_divizibilitate",
        "title": "21. Criterii de divizibilitate",
        "icon": "📏",
        "keywords": ["criteriul cu 2", "criteriul cu 5", "criteriul cu 3", "criteriul cu 9", "zecimal", "criteriu", "criterii", "divizibil cu", "se imparte la", "se divide cu"],
        "lessons": [
            "Criteriul cu 2: Ultima cifră e 0,2,4,6,8.",
            "Criteriul cu 5: Ultima cifră e 0 sau 5.",
            "Criteriul cu 3: Suma cifrelor este divizibilă cu 3."
        ],
        "exercises": [
            {"question": "Este 4536 divizibil cu 9?", "answer": "da"},
            {"question": "Care este cel mai mic număr de 3 cifre divizibil cu 5?", "answer": "100"},
            {"question": "Este 231 divizibil cu 3?", "answer": "da"}
        ],
        "fun_facts": [
            "📏 Criteriul cu 3 se bazează pe faptul că 10 dă restul 1 la împărțirea cu 3!",
            "🎩 Poți verifica instant dacă un număr imens se divide cu 9!"
        ]
    },
    {
        "id": "numere_prime_compuse",
        "title": "22. Numere Prime și Compuse",
        "icon": "🧱",
        "keywords": ["numar prim", "numar compus", "Eratostene", "491", "factori primi", "prim", "compus", "ciurul", "prime"],
        "lessons": [
            "Număr Prim: Are exact 2 divizori (1 și el însuși). Singurul prim par e 2.",
            "Număr Compus: Are cel puțin 3 divizori.",
            "! 0 și 1 nu sunt nici prime, nici compuse."
        ],
        "exercises": [
            {"question": "Scrie numerele prime între 12 și 38.", "answer": "13, 17, 19, 23, 29, 31, 37"},
            {"question": "Este 289 număr prim?", "answer": "nu"},
            {"question": "Care este cel mai mic număr prim?", "answer": "2"}
        ],
        "fun_facts": [
            "🧱 Numerele prime sunt 'atomii' matematicii!",
            "🏆 Cel mai mare număr prim are peste 41 de milioane de cifre!"
        ]
    }
]

# Scrie datele în fișier
with open('data/chapters.json', 'w', encoding='utf-8') as f:
    json.dump(chapters, f, ensure_ascii=False, indent=4)
print("SUCCESS: chapters.json successfully rewritten via Python.")
