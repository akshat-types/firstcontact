"""CSV contracts and deterministic PRESSIQ metrics; no network or UI required."""
from pathlib import Path
import pandas as pd

FLAGS = ['counterpress_opportunity', 'quick_regain', 'high_regain', 'disrupted',
         'press_escaped', 'duels_won', 'duels_contested', 'second_ball_win',
         'second_ball_contested', 'shot_after_regain']

def load_data(directory):
    names = ['synthetic_match.csv', 'pressiq_tactics.csv', 'pressiq_insights.csv']
    frames = []
    for name in names:
        path = Path(directory) / name
        if not path.is_file():
            raise ValueError(f'Missing {path}. Run the earlier generator/analysis cells first.')
        try:
            frames.append(pd.read_csv(path))
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
            raise ValueError(f'{name} is empty or malformed.') from exc
    events, tactics, insights = frames
    contracts = [(['sequence_id', 'timestamp', 'team', 'event_type', 'x', 'y'], events),
                 (['sequence_id', 'minute', 'team', 'outcome'] + FLAGS, tactics),
                 (['minute', 'team', 'outcome', 'explanation'], insights)]
    for name, (required, frame) in zip(names, contracts):
        missing = set(required) - set(frame.columns)
        if missing:
            raise ValueError(f'{name}: missing columns {", ".join(sorted(missing))}')
        if frame.empty:
            raise ValueError(f'{name} has no rows.')
    for frame in (events, tactics):
        if frame.sequence_id.isna().any():
            raise ValueError('Sequence IDs must not be empty.')
        frame['sequence_id'] = frame.sequence_id.astype(str)
    for col in ['timestamp', 'x', 'y']:
        events[col] = pd.to_numeric(events[col], errors='coerce')
    if events[['timestamp', 'x', 'y']].isna().any().any() or (events.timestamp < 0).any():
        raise ValueError('Event timestamp/x/y must be numeric; timestamps must be nonnegative.')
    if not events[['x', 'y']].apply(lambda s: s.between(0, 100)).all().all():
        raise ValueError('Pitch coordinates must be between 0 and 100.')
    for col in FLAGS + ['minute']:
        tactics[col] = pd.to_numeric(tactics[col], errors='coerce')
    insights['minute'] = pd.to_numeric(insights.minute, errors='coerce')
    if tactics[FLAGS + ['minute']].isna().any().any() or insights.minute.isna().any():
        raise ValueError('Tactical metrics and insight minutes must be numeric.')
    if (tactics[FLAGS] < 0).any().any() or tactics.sequence_id.duplicated().any():
        raise ValueError('Tactical counts must be nonnegative, with one row per sequence.')
    ends = events.groupby('sequence_id').timestamp.max().rename('completed_at')
    tactics = tactics.merge(ends, on='sequence_id', how='left', validate='one_to_one')
    if tactics.completed_at.isna().any():
        raise ValueError('A tactical sequence has no matching events.')
    # Original insight export has no sequence_id: link by its original rounded minute/team/outcome.
    if 'sequence_id' not in insights:
        keys = ['minute', 'team', 'outcome']
        left, right = insights.copy(), tactics.copy()
        left['_occ'] = left.groupby(keys).cumcount()
        right['_occ'] = right.groupby(keys).cumcount()
        insights = left.merge(right[keys + ['_occ', 'sequence_id']], on=keys + ['_occ'], how='left')
    else:
        insights['sequence_id'] = insights.sequence_id.astype(str)
    if insights.sequence_id.isna().any():
        raise ValueError('Insights do not match tactics. Regenerate both exports together.')
    return events.sort_values('timestamp', kind='stable').reset_index(drop=True), tactics, insights

def percentage(n, d):
    return 100 * n / d if d else 0.0

def scores(data, teams):
    rows = []
    for team in teams:
        g = data[data.team == team]
        n = len(g)
        cpr = percentage(g.quick_regain.sum(), g.counterpress_opportunity.sum())
        high = percentage(g.high_regain.sum(), n)
        disruption = percentage(g.disrupted.sum(), n)
        duel = percentage(g.duels_won.sum(), g.duels_contested.sum())
        shot = percentage(((g.high_regain == 1) & (g.shot_after_regain == 1)).sum(), g.high_regain.sum())
        second = percentage(g.second_ball_win.sum(), g.second_ball_contested.sum())
        denied = percentage(n - g.press_escaped.sum(), n)
        rows.append({'Team': team, 'Presses': n, 'Counterpress %': cpr, 'High turnover %': high,
                     'Disruption %': disruption, 'Duel win %': duel, 'Press-to-shot %': shot,
                     'Second ball %': second, 'Denied escape %': denied,
                     'Lijnders Score': .35*cpr + .30*shot + .20*high + .15*second,
                     'Arteta Score': .35*disruption + .25*high + .20*duel + .20*denied})
    return pd.DataFrame(rows).round(1)

def narrative(row, persona):
    if persona == 'Analyst':
        return (f"{row['team']} · {row['outcome']}. Quick regain: {int(row['quick_regain'])}; "
                f"high regain: {int(row['high_regain'])}; duels won/recorded contests: "
                f"{int(row['duels_won'])}/{int(row['duels_contested'])}; "
                f"shot within 10s of regain: {int(row['shot_after_regain'])}.")
    return {
        'Attacking counterpress': 'Won it back within five seconds of losing it, then created a shot.',
        'Press bypassed': 'The opposition escaped the pressure.',
        'High regain leading to shot': 'Recovered the ball and created a shot within ten seconds.',
        'Recovery without immediate shot': 'Won the ball back, but no shot followed within ten seconds.',
        'Press disrupted buildup': 'Disrupted the buildup without a confirmed recovery.',
        'Unsuccessful press': 'No confirmed recovery or buildup disruption followed the pressure.'
    }.get(row['outcome'], str(row['outcome']))
