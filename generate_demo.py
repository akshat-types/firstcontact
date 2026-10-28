"""Reproducible, fictional demo data. Never replaces the user's Colab exports."""
import argparse
from pathlib import Path
import random
import pandas as pd
from pressiq_core import narrative

def generate(directory, sequences=72, seed=42):
    rng = random.Random(seed)
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    events, tactics, insights = [], [], []
    teams = ['North City', 'East Borough']
    for sid in range(1, sequences+1):
        team = teams[(sid-1) % 2]
        opponent = next(t for t in teams if t != team)
        scenario = rng.choices(['counterpress','high_shot','recovery','bypassed','disruption','unsuccessful'],
                               weights=([28,20,18,17,12,5] if team == teams[0] else [15,18,18,28,13,8]))[0]
        start = (sid-1)*75
        x, y = round(rng.uniform(55,84),1), round(rng.uniform(20,80),1)
        if scenario == 'high_shot':
            x = max(70,x)
        group = []
        def add(offset, actor, kind, possession=None, success=None, duel='', outcome='', loc=None):
            group.append({'timestamp':round(start+offset,2), 'sequence_id':sid, 'team':actor,
                          'player_id':('NC' if actor==teams[0] else 'EB')+f'_{rng.randint(1,11):02}',
                          'event_type':kind, 'possession_team':possession, 'x':x if loc is None else loc,
                          'y':y, 'success':success, 'duel_type':duel, 'outcome':outcome})
        if scenario == 'counterpress':
            add(0,team,'possession_loss',opponent)
            add(1,team,'pressure',opponent)
            add(2.5,opponent,'clearance')
            add(3.5,team,'duel',success=True,duel='second_ball')
            add(4.2,team,'recovery',team,loc=x+3)
            add(8,team,'shot',opponent,success=True,outcome='shot_created',loc=90)
        elif scenario == 'high_shot':
            add(0,opponent,'backward_pass',opponent)
            add(1,team,'pressure',opponent)
            add(3,opponent,'clearance')
            add(4,team,'duel',success=True,duel='aerial')
            add(5,team,'recovery',team)
            add(10,team,'shot',opponent,success=True,outcome='shot_created',loc=90)
        elif scenario == 'recovery':
            add(1,team,'pressure',opponent)
            add(2,team,'duel',success=True,duel='ground')
            add(3,team,'recovery',team)
            add(9,team,'backward_pass',team,loc=45)
        elif scenario == 'bypassed':
            if rng.random()<.5:
                add(0,team,'possession_loss',opponent)
            add(1,team,'pressure',opponent)
            add(3,opponent,'duel',opponent,success=True,duel='ground')
            add(5,opponent,'pass',opponent,success=True,outcome='press_escaped',loc=45)
            add(9,opponent,'carry',opponent,loc=25)
        elif scenario == 'disruption':
            add(1,team,'pressure',opponent)
            add(4,opponent,'backward_pass',opponent,loc=40)
            add(7,opponent,'clearance',loc=30)
        else:
            add(1,team,'pressure',opponent)
            add(4,opponent,'pass',opponent)
            add(7,opponent,'pass',opponent)
        events.extend(group)
        regain = next((e for e in group if e['event_type']=='recovery' and e['team']==team),None)
        loss = next((e for e in group if e['event_type']=='possession_loss' and e['team']==team),None)
        quick = bool(regain and loss and 0<=regain['timestamp']-loss['timestamp']<=5)
        shot = bool(regain and any(e['event_type']=='shot' and e['team']==team and
                                   0<e['timestamp']-regain['timestamp']<=10 for e in group))
        high = bool(regain and regain['x']>=66.7)
        escaped = scenario=='bypassed'
        disrupted = not escaped and (regain is not None or scenario=='disruption')
        outcome = ('Attacking counterpress' if quick and shot else 'Press bypassed' if escaped else
                   'High regain leading to shot' if high and shot else
                   'Recovery without immediate shot' if regain else
                   'Press disrupted buildup' if disrupted else 'Unsuccessful press')
        duels = [e for e in group if e['event_type']=='duel']
        row = {'sequence_id':sid,'minute':round((start+1)/60,1),'team':team,'press_x':x,
               'counterpress_opportunity':int(loss is not None),'quick_regain':int(quick),
               'high_regain':int(high),'disrupted':int(disrupted),'press_escaped':int(escaped),
               'duels_won':sum(e['team']==team and e['success'] is True for e in duels),
               'duels_contested':len(duels),
               'second_ball_win':int(any(e['team']==team and e['duel_type']=='second_ball' for e in duels)),
               'second_ball_contested':int(any(e['duel_type']=='second_ball' for e in duels)),
               'shot_after_regain':int(shot),'outcome':outcome}
        tactics.append(row)
        insights.append({'sequence_id':sid,'minute':row['minute'],'team':team,'outcome':outcome,
                         'explanation':narrative(row,'Casual fan')})
    for name, records in [('synthetic_match',events),('pressiq_tactics',tactics),('pressiq_insights',insights)]:
        pd.DataFrame(records).to_csv(target/f'{name}.csv',index=False)
    (target/'DEMO_DATA.md').write_text(f'''# Bundled demonstration match

Generated with `python generate_demo.py --output data --seed {seed} --sequences {sequences}`.
Fictional North City vs East Borough; scripted scenarios with seeded variation.
These files are newly generated demo data, not the user's original Colab exports.
Coordinates use each sequence's pressing direction. Duel rows record winners.
They are suitable for demonstrating software behavior, not validating real tactics.
''',encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='data')
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--sequences',type=int,default=72)
    args=parser.parse_args()
    if args.sequences<1:
        parser.error('--sequences must be positive')
    generate(args.output,args.sequences,args.seed)
