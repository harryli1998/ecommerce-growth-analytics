"""Budget-sensitive, paired evaluation of fixed historical ranking policies."""
import math
import numpy as np
import pandas as pd


def policy_comparison(frame, fractions=(.05, .1, .2, .4), draws=1000, seed=42):
    """Customer bootstrap conditional on a fitted model; no refitting or causal claim."""
    if frame.customer_id.duplicated().any():
        raise ValueError('One row per customer per snapshot is required')
    if frame.empty or not frame.returned.isin([0, 1]).all():
        raise ValueError('Nonempty binary outcomes required')
    # Sorting by ID supplies a deterministic, label-independent tie break.
    frame = frame.sort_values('customer_id').reset_index(drop=True)
    y = frame.returned.to_numpy()
    scores = {'Model': frame.probability.to_numpy(), 'Recency': -frame.recency.to_numpy()}
    if not all(np.isfinite(s).all() for s in scores.values()):
        raise ValueError('Scores must be finite')
    rng = np.random.default_rng(seed)
    rows = []
    for fraction in fractions:
        if not 0 < fraction <= 1:
            raise ValueError('Budget fractions must be in (0, 1]')
        n = math.ceil(len(frame) * fraction)
        precisions = {k: y[np.argsort(-v, kind='stable')[:n]].mean() for k, v in scores.items()}
        differences = []
        for _ in range(draws):
            idx = rng.integers(0, len(y), len(y))
            # Paired resampling: both policies see the same customer sample.
            rates = [y[idx][np.argsort(-v[idx], kind='stable')[:n]].mean() for v in scores.values()]
            differences.append(rates[0] - rates[1])
        low, high = np.quantile(differences, [.025, .975])
        rows.append({'budget_fraction': fraction, 'selected_customers': n,
                     'model_precision': precisions['Model'], 'recency_precision': precisions['Recency'],
                     'random_expected_precision': y.mean(),
                     'precision_difference': precisions['Model'] - precisions['Recency'],
                     'difference_ci_low': low, 'difference_ci_high': high,
                     'bootstrap_draws': draws, 'seed': seed})
    return pd.DataFrame(rows)
