import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from pressiq_core import FLAGS, load_data, scores

def fixture(folder):
    rows = []
    for seq, team, outcome, start in [(1,'North City','Attacking counterpress',0),
                                       (2,'East Borough','Press bypassed',20)]:
        for offset, kind in [(0,'possession_loss'),(1,'pressure'),(3,'duel'),(4,'recovery'),(8,'shot')]:
            rows.append(dict(sequence_id=seq,timestamp=start+offset,team=team,event_type=kind,
                             x=75,y=50,success=True,duel_type='second_ball'))
    pd.DataFrame(rows).to_csv(Path(folder)/'synthetic_match.csv',index=False)
    tactics=[]
    insights=[]
    for seq, team, outcome, minute in [(1,'North City','Attacking counterpress',0.0),
                                       (2,'East Borough','Press bypassed',0.3)]:
        row=dict(sequence_id=seq,team=team,outcome=outcome,minute=minute)
        row.update({f: int(seq==1) for f in FLAGS})
        row.update(counterpress_opportunity=1,duels_contested=1,second_ball_contested=1,press_escaped=int(seq==2))
        tactics.append(row)
        insights.append(dict(minute=minute,team=team,outcome=outcome,explanation='Saved evidence'))
    pd.DataFrame(tactics).to_csv(Path(folder)/'pressiq_tactics.csv',index=False)
    pd.DataFrame(insights).to_csv(Path(folder)/'pressiq_insights.csv',index=False)

class EngineTests(unittest.TestCase):
    def test_bundled_demo(self):
        events, tactics, insights = load_data(Path(__file__).parent / 'data')
        self.assertEqual(len(tactics), 72)
        self.assertEqual(set(tactics.sequence_id), set(insights.sequence_id))
        self.assertEqual(set(tactics.sequence_id), set(events.sequence_id))
        self.assertEqual(tactics.outcome.nunique(), 6)
        result = scores(tactics, sorted(events.team.unique()))
        self.assertTrue(result[['Lijnders Score', 'Arteta Score']].map(lambda x: 0 <= x <= 100).all().all())

    def test_contract_and_scores(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            fixture(tmp)
            events,tactics,insights=load_data(tmp)
            self.assertEqual(list(tactics.completed_at),[8,28])
            self.assertEqual(list(insights.sequence_id),['1','2'])
            result=scores(tactics,['North City','East Borough']).set_index('Team')
            self.assertEqual(result.loc['North City','Lijnders Score'],100)
            self.assertEqual(result.loc['East Borough','Arteta Score'],0)
            self.assertEqual(scores(tactics.iloc[:0],['North City']).iloc[0]['Arteta Score'],0)

    def test_missing_files_and_bad_numeric(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            with self.assertRaises(ValueError): load_data(tmp)
            fixture(tmp)
            path=Path(tmp)/'synthetic_match.csv'
            data=pd.read_csv(path)
            data.loc[0,'x']=101
            data.to_csv(path,index=False)
            with self.assertRaisesRegex(ValueError,'coordinates'):load_data(tmp)

    def test_streamlit_replay(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            fixture(tmp)
            self.addCleanup(patch.stopall)
            patch.dict(os.environ, {'PRESSIQ_DATA_DIR':tmp}).start()
            at=AppTest.from_file('app.py',default_timeout=30).run()
            self.assertFalse(at.exception)
            self.assertEqual(at.metric[2].value,'0')
            at.button[2].click().run()  # next
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state['cursor'],1)
            at.slider[0].set_value(9).run()
            self.assertFalse(at.exception)
            self.assertEqual(at.metric[2].value,'2')
            at.radio[0].set_value('Analyst').run()
            at.checkbox[0].check().run()
            self.assertFalse(at.exception)
            self.assertTrue(any('not configured' in c.value for c in at.caption))
            at.button[3].click().run()  # restart
            self.assertEqual(at.session_state['cursor'],0)
            self.assertEqual(at.metric[2].value,'0')

if __name__=='__main__':unittest.main()
