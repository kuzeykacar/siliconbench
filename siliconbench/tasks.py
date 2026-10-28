"""University-style problems with fresh random numbers and an automatic checker.
Every problem exists in English and in Italian, with the same numbers, so the language gap can be measured directly.
Nothing comes from an external dataset: the generators are written here from standard textbook formulas."""
import math, random, re

class Task:
    def __init__(self, subject, tid, lang, prompt, check, answer, max_tokens=512):
        self.subject, self.id, self.lang, self.prompt, self.check, self.answer = subject, tid, lang, prompt, check, answer
        self.max_tokens = max_tokens

NUM = r"[-+]?\d[\d.,]*(?:\s*[x×*·]\s*10\s*\^?\s*[-+]?\d+|[eE][-+]?\d+)?"

def _to_float(s):
    """'3,021.5' -> 3021.5, '3.021,5' -> 3021.5, '1,5' -> 1.5, '1,500' -> 1500."""
    s = s.rstrip(".,")
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if dec == "," else ",", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", "") if re.fullmatch(r"[-+]?\d{1,3}(,\d{3})+", s) else s.replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    return float(s)

def parse_last_number(text):
    """Last number in the answer (looks at the last lines first). Handles 1.5e-3, 1,5 and 1.5 x 10^-3."""
    text = text.replace("−", "-").replace("**", "")
    tail = text.strip().splitlines()[-3:] if text.strip() else []
    for chunk in (" ".join(tail), text):
        found = re.findall(NUM, chunk)
        if found:
            s = found[-1].replace(" ", "")
            m = re.match(r"([-+]?\d[\d.,]*)[x×*·]10\^?([-+]?\d+)", s)
            try:
                return _to_float(m.group(1)) * 10 ** int(m.group(2)) if m else (
                    _to_float(s.split("e")[0].split("E")[0]) * 10 ** int(re.split("[eE]", s)[1]) if re.search("[eE]", s) else _to_float(s))
            except (ValueError, IndexError):
                return None
    return None

def close(rel=0.02):
    def make(ans):
        def check(text):
            v = parse_last_number(text)
            return v is not None and abs(v - ans) <= rel * max(abs(ans), 1e-12)
        return check
    return make

TAIL = {"en": "Show your reasoning briefly. On the last line write only the final number.",
        "it": "Mostra brevemente il ragionamento. Nell'ultima riga scrivi solo il numero finale."}

def pair(subject, i, en, it, ans, rel=0.02):
    """Same problem in both languages. Italian text uses the decimal comma (0,05 instead of 0.05)."""
    it = re.sub(r"(?<=\d)\.(?=\d)", ",", it)
    chk = close(rel)(ans)
    return [Task(subject, f"{subject[:4]}{i:03d}", "en", en + "\n" + TAIL["en"], chk, ans),
            Task(subject, f"{subject[:4]}{i:03d}", "it", it + "\n" + TAIL["it"], chk, ans)]

K = 8.99e9
def physics(n, rng):
    out = []
    for i in range(n):
        kind = i % 3
        if kind == 0:
            q1, q2, r = rng.randint(2, 9), rng.randint(2, 9), rng.choice([0.05, 0.1, 0.2, 0.3])
            ans = K * q1 * 1e-6 * q2 * 1e-6 / r ** 2
            en = f"Two point charges of {q1} µC and {q2} µC are {r} m apart in vacuum. What is the magnitude of the electric force between them, in newtons? Use k = 8.99e9 N·m²/C²."
            it = f"Due cariche puntiformi di {q1} µC e {q2} µC si trovano a {r} m di distanza nel vuoto. Qual è il modulo della forza elettrica tra di loro, in newton? Usa k = 8,99e9 N·m²/C²."
        elif kind == 1:
            q, r = rng.randint(1, 9), rng.choice([0.1, 0.25, 0.5, 2.0])
            ans = K * q * 1e-9 / r ** 2
            en = f"What is the magnitude of the electric field at {r} m from a point charge of {q} nC, in N/C? Use k = 8.99e9 N·m²/C²."
            it = f"Qual è il modulo del campo elettrico a {r} m da una carica puntiforme di {q} nC, in N/C? Usa k = 8,99e9 N·m²/C²."
        else:
            sigma = rng.randint(1, 9)
            ans = sigma * 1e-6 / (2 * 8.854e-12)
            en = f"An infinite plane carries a uniform surface charge density of {sigma} µC/m². What is the magnitude of its electric field, in N/C? Use ε0 = 8.854e-12 F/m."
            it = f"Un piano infinito ha una densità superficiale di carica uniforme di {sigma} µC/m². Qual è il modulo del suo campo elettrico, in N/C? Usa ε0 = 8,854e-12 F/m."
        out += pair("physics", i, en, it, ans)
    return out

def macro(n, rng):
    out = []
    for i in range(n):
        kind = i % 3
        c0, c1, I, G, T = rng.randint(100, 300), rng.choice([0.5, 0.6, 0.75, 0.8]), rng.randint(100, 300), rng.randint(100, 400), rng.randint(50, 300)
        if kind == 0:
            ans = (c0 - c1 * T + I + G) / (1 - c1)
            en = f"In the goods market model, C = {c0} + {c1}·(Y − T), I = {I}, G = {G}, T = {T}. What is equilibrium output Y?"
            it = f"Nel modello del mercato dei beni, C = {c0} + {c1}·(Y − T), I = {I}, G = {G}, T = {T}. Qual è la produzione di equilibrio Y?"
        elif kind == 1:
            dG = rng.randint(10, 80); ans = dG / (1 - c1)
            en = f"With a marginal propensity to consume of {c1}, government spending rises by {dG}. By how much does equilibrium output increase?"
            it = f"Con una propensione marginale al consumo pari a {c1}, la spesa pubblica aumenta di {dG}. Di quanto aumenta la produzione di equilibrio?"
        else:
            dT = rng.randint(10, 80); ans = -c1 * dT / (1 - c1)
            en = f"With a marginal propensity to consume of {c1}, taxes rise by {dT}. What is the change in equilibrium output (negative if it falls)?"
            it = f"Con una propensione marginale al consumo pari a {c1}, le tasse aumentano di {dT}. Qual è la variazione della produzione di equilibrio (negativa se diminuisce)?"
        out += pair("macro", i, en, it, ans)
    return out

def comparch(n, rng):
    out = []
    for i in range(n):
        kind = i % 3
        if kind == 0:
            instr, cpi, ghz = rng.choice([1e6, 5e6, 2e7, 1e8]), rng.choice([1.5, 2, 3, 4]), rng.choice([1, 2, 2.5, 4])
            ans = instr * cpi / (ghz * 1e9) * 1e3
            en = f"A program executes {instr / 1e6:g} million instructions with an average CPI of {cpi} on a {ghz} GHz processor. What is the execution time in milliseconds?"
            it = f"Un programma esegue {instr / 1e6:g} milioni di istruzioni con un CPI medio di {cpi} su un processore a {ghz} GHz. Qual è il tempo di esecuzione in millisecondi?"
        elif kind == 1:
            x = rng.randint(40, 250); b = format(x, "b"); ans = x
            en = f"Convert the unsigned binary number {b} to decimal."
            it = f"Converti in decimale il numero binario senza segno {b}."
        else:
            bits = rng.choice([16, 20, 24, 32]); ans = 2 ** bits / 2 ** 20
            en = f"A byte-addressable memory has a {bits}-bit address bus. How many mebibytes (MiB) can it address?"
            it = f"Una memoria indirizzabile al byte ha un bus indirizzi di {bits} bit. Quanti mebibyte (MiB) può indirizzare?"
        out += pair("comparch", i, en, it, ans, rel=0.001)
    return out

def mathecon(n, rng):
    out = []
    for i in range(n):
        kind = i % 3
        if kind == 0:
            a, b, c, x = rng.randint(1, 5), rng.randint(2, 9), rng.randint(1, 9), rng.randint(1, 4)
            ans = 3 * a * x ** 2 - 2 * b * x + c
            en = f"Let f(x) = {a}x³ − {b}x² + {c}x. Compute f'({x})."
            it = f"Sia f(x) = {a}x³ − {b}x² + {c}x. Calcola f'({x})."
        elif kind == 1:
            P, r, t = rng.choice([1000, 2500, 5000]), rng.choice([2, 3, 4, 5]), rng.randint(2, 10)
            ans = P * (1 + r / 100) ** t
            en = f"You invest {P} euros at {r}% annual compound interest for {t} years. What is the final amount in euros?"
            it = f"Investi {P} euro al {r}% di interesse composto annuo per {t} anni. Qual è il montante finale in euro?"
        else:
            C0, cf, r = rng.choice([1000, 2000, 3000]), rng.choice([400, 600, 900, 1200]), rng.choice([5, 8, 10])
            ans = -C0 + sum(cf / (1 + r / 100) ** k for k in (1, 2, 3))
            en = f"A project costs {C0} euros today and pays {cf} euros at the end of each of the next 3 years. With a {r}% discount rate, what is its NPV in euros?"
            it = f"Un progetto costa {C0} euro oggi e rende {cf} euro alla fine di ciascuno dei prossimi 3 anni. Con un tasso di sconto del {r}%, qual è il suo VAN in euro?"
        out += pair("mathecon", i, en, it, ans, rel=0.005)
    return out

# Italian grammar (multiple choice); the question is in English or Italian, the options are always Italian.
GRAMMAR = [
    ("Paola ___ a Milano due anni fa.", ["ha trasferito", "si ha trasferito", "si è trasferita", "è trasferito"], 2),
    ("Ieri noi ___ al cinema.", ["abbiamo andato", "siamo andati", "siamo andato", "avete andati"], 1),
    ("Quanti amici hai? ___ ho quattro.", ["Li", "Ne", "Ci", "Gli"], 1),
    ("Il plurale di 'il braccio' è ___.", ["i bracci", "le braccia", "le bracce", "gli bracci"], 1),
    ("Il caffè è più buono ___ tè.", ["di", "del", "che il", "dal"], 1),
    ("Domani alle 17 io ___ lezione.", ["starò facendo", "sarò facendo", "starei fatto", "ho fatto"], 0),
    ("Puoi aiutare Paola? Sì, ___ aiuto io.", ["le", "la", "gli", "lo"], 1),
    ("Quando ero piccolo ___ sempre con mia nonna.", ["ho giocato", "giocavo", "giocherò", "gioco stato"], 1),
    ("La casa ___ abitiamo è grande.", ["che", "in cui", "cui che", "dove che"], 1),
    ("Non ___ potuto pranzare oggi.", ["sono", "ho", "abbiamo stato", "sei"], 1),
    ("Signora, ___ prima, per favore!", ["paga", "paghi", "pagi", "paghe"], 1),
    ("Il plurale di 'il problema' è ___.", ["le probleme", "i problemi", "i problema", "le problemi"], 1),
]
def grammar(n, rng):
    out = []
    for i, (s, opts, k) in enumerate(GRAMMAR[:n]):
        letters = "ABCD"; o = "\n".join(f"{letters[j]}) {x}" for j, x in enumerate(opts))
        def chk(text, k=k):
            m = re.findall(r"\b([ABCD])\b", text.strip().splitlines()[-1] if text.strip() else "")
            return bool(m) and m[-1] == "ABCD"[k]
        en = f"Choose the correct option to complete the Italian sentence:\n{s}\n{o}\nOn the last line write only the letter."
        it = f"Scegli l'opzione corretta per completare la frase:\n{s}\n{o}\nNell'ultima riga scrivi solo la lettera."
        out += [Task("grammar", f"gram{i:03d}", "en", en, chk, "ABCD"[k], 200), Task("grammar", f"gram{i:03d}", "it", it, chk, "ABCD"[k], 200)]
    return out

SUBJECTS = {"physics": physics, "macro": macro, "comparch": comparch, "mathecon": mathecon, "grammar": grammar}

def build(n_per_subject=12, seed=0, subjects=None):
    rng = random.Random(seed); tasks = []
    for name in subjects or SUBJECTS:
        tasks += SUBJECTS[name](n_per_subject, rng)
    return tasks
