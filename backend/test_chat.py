import asyncio
import httpx
import json

async def test_chat():
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Login first
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = await client.post('http://127.0.0.1:8001/api/auth/login', data=login_data)
        if response.status_code != 200:
            print('Login failed:', response.text)
            return
        
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test database question
        print('=== Test 1: Database question ===')
        chat_data = {'message': 'Combien de stagiaires sont actuellement en stage ?', 'conversation_id': None}
        response = await client.post('http://127.0.0.1:8001/api/chat', json=chat_data, headers=headers)
        print('Response:', json.dumps(response.json(), ensure_ascii=False, indent=2))
        
        # Test RAG question
        print('\n=== Test 2: RAG question ===')
        chat_data = {'message': "Quelle est la procédure de validation d'un rapport ?", 'conversation_id': None}
        response = await client.post('http://127.0.0.1:8001/api/chat', json=chat_data, headers=headers)
        print('Response:', json.dumps(response.json(), ensure_ascii=False, indent=2))
        
        # Test hybrid question
        print('\n=== Test 3: Hybrid question ===')
        chat_data = {'message': "Quelle est la note de Seif et comment fonctionne l'évaluation ?", 'conversation_id': None}
        response = await client.post('http://127.0.0.1:8001/api/chat', json=chat_data, headers=headers)
        print('Response:', json.dumps(response.json(), ensure_ascii=False, indent=2))

asyncio.run(test_chat())