import time
from openrouter_service import generate_chat_completion

print("1. Primeira chamada (inicializa conexao e identifica modelo ativo)...")
t0 = time.time()
res1 = generate_chat_completion("Voce e conciso.", "Diga apenas: Pronto 1.", max_tokens=20)
d1 = round(time.time() - t0, 2)
print(f"-> Concluído em {d1}s: {res1}")

print("\n2. Segunda chamada (reutiliza conexao Keep-Alive e modelo memorizado)...")
t1 = time.time()
res2 = generate_chat_completion("Voce e conciso.", "Diga apenas: Pronto 2.", max_tokens=20)
d2 = round(time.time() - t1, 2)
print(f"-> Concluído em {d2}s: {res2}")

print(f"\nAceleracao obtida: a segunda chamada foi executada em {d2}s!")
