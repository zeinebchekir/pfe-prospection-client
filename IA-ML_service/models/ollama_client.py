import ollama

# Connexion à Ollama dans Docker
client = ollama.Client(host='http://ollama:11434')

def test_analyse():
    print("🚀 Envoi de la requête à Qwen2.5:7b... (patiente un instant)")
    
    response = client.chat(
        model='qwen2.5:7b', # <-- On utilise bien le 7b ici !
        messages=[
            {'role': 'user', 'content': 'Fais un résumé en 2 phrases de la Métropole Aix Marseille Provence.'}
        ]
    )
    
    print("\n✅ Résultat :")
    print(response['message']['content'])

if __name__ == "__main__":
    test_analyse()