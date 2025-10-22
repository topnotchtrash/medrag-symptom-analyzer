def stop_condition(ddx, min_top_score=0.88, delta=0.05):
    if not ddx: return False
    top = ddx[0]['score']
    if top >= min_top_score: return True
    if len(ddx)>1 and (top - ddx[1]['score']) >= delta: return True
    return False
