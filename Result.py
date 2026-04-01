def calculate_final_score(user_answers, question_bank):
    stats = {
        "Total": {"score": 0, "correct": 0, "wrong": 0},
        "Physics": {"score": 0, "correct": 0, "wrong": 0},
        "Chemistry": {"score": 0, "correct": 0, "wrong": 0},
        "Maths": {"score": 0, "correct": 0, "wrong": 0}
    }
    for q in question_bank:
        q_id = q['q_id']
        u_ans = user_answers.get(q_id)
        sub = q.get('subject', 'Physics') # Firebase key check
        
        if u_ans == q.get('correct'):
            stats["Total"]["correct"] += 1
            stats["Total"]["score"] += 4
            if sub in stats:
                stats[sub]["correct"] += 1
                stats[sub]["score"] += 4
        elif u_ans not in [None, "None"]:
            stats["Total"]["wrong"] += 1
            stats["Total"]["score"] -= 1
            if sub in stats:
                stats[sub]["wrong"] += 1
                stats[sub]["score"] -= 1
    return stats