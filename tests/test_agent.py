from services.agent import DiagnosticAgent

def test_agent_runs():
    agent = DiagnosticAgent()
    ddx = agent.rank_diseases(['cough','fever'], [
        {'disease_id':'pneumonia','disease_name':'Pneumonia','score':0.8,'reasons':['cough','fever']},
        {'disease_id':'bronchitis','disease_name':'Bronchitis','score':0.7,'reasons':['cough']},
    ])
    assert ddx and ddx[0]['disease_id'] in ('pneumonia','bronchitis')
