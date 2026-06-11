import sys

import json
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
sys.path.append('/home/matt/Proj/Hermetica')
from OntoLLM import OntoLLMv2

models= ['llama2', 'llama3.1', 'llama3.2', 'phi','phi3','phi3.5']


models = ['phi4','llama 3.2','deepseek-r1']
for model in models:

    llm = ChatOllama(
        model=model,
        temperature=0
    )

    Core = OntoLLMv2.OntoLLM(LLM = model)
    with open('/home/matt/Proj/Hermetica/Testing/PolymerScienceQuestions.json', 'r') as file:
        questions=json.load(file)

    data = []
    i = 0

    name = model.replace('.','')

    for s in questions:
        for j in questions[s]:
            q = j['question']
            response = llm.invoke(q)

            redo, info=Core.Process(q,response.content)
            toadd = {'number':i,'question':q,f'{name}Response':response.content,'HermeticaResponse':redo, 'sentenceinfo':info}
            data.append(dict(toadd))
            i+=1
            with open(f'/home/matt/Proj/Hermetica/Testing/Results/OpenQsResults/ShortPrompt/{name}PolyQA.json','w', encoding='utf-8') as f:
                #d = json.dumps(data)
                json.dump(data, f)
            print(i)