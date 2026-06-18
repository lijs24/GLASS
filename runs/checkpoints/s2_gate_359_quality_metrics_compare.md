# GLASS Quality Metrics Compare

- Status: failed
- Baseline: runs\checkpoints\s2_gate_359_quality_metrics_baseline_frame_quality.json
- Candidate: runs\checkpoints\s2_gate_359_quality_metrics_candidate_frame_quality.json
- Baseline metrics: ['star_count', 'fwhm_px', 'eccentricity', 'background_rms', 'snr', 'quality_score', 'weight']
- Candidate metrics: ['star_count', 'fwhm_px', 'eccentricity', 'background_rms', 'snr', 'quality_score', 'weight']

## Checks

- PASS: baseline_frame_quality_available - {'path': 'runs\\checkpoints\\s2_gate_359_quality_metrics_baseline_frame_quality.json', 'status': 'passed', 'frame_count': 2, 'metric_count': 7}
- PASS: candidate_frame_quality_available - {'path': 'runs\\checkpoints\\s2_gate_359_quality_metrics_candidate_frame_quality.json', 'status': 'passed', 'frame_count': 2, 'metric_count': 7}
- PASS: candidate_metric_summary_preserved - {'missing_metrics': [], 'baseline_metrics': ['star_count', 'fwhm_px', 'eccentricity', 'background_rms', 'snr', 'quality_score', 'weight'], 'candidate_metrics': ['star_count', 'fwhm_px', 'eccentricity', 'background_rms', 'snr', 'quality_score', 'weight']}
- FAIL: bad_median_ratio_within_limit - {'max_bad_median_ratio': 1.2, 'failing_metrics': [{'metric': 'fwhm_px', 'bad_median_ratio': 1.4, 'baseline_median': 2.5, 'candidate_median': 3.5}, {'metric': 'eccentricity', 'bad_median_ratio': 1.4, 'baseline_median': 0.4, 'candidate_median': 0.56}, {'metric': 'background_rms', 'bad_median_ratio': 1.4, 'baseline_median': 25.0, 'candidate_median': 35.0}, {'metric': 'snr', 'bad_median_ratio': 1.4, 'baseline_median': 45.0, 'candidate_median': 32.142857}, {'metric': 'quality_score', 'bad_median_ratio': 1.4, 'baseline_median': 800.0, 'candidate_median': 571.428571}, {'metric': 'weight', 'bad_median_ratio': 1.399999, 'baseline_median': 0.8, 'candidate_median': 0.571429}]}

## Metrics

- star_count: baseline_median=90.0 candidate_median=90.0 bad_median_ratio=1.0 baseline_mean=90.0 candidate_mean=90.0 bad_mean_ratio=1.0
- fwhm_px: baseline_median=2.5 candidate_median=3.5 bad_median_ratio=1.4 baseline_mean=2.5 candidate_mean=3.5 bad_mean_ratio=1.4
- eccentricity: baseline_median=0.4 candidate_median=0.56 bad_median_ratio=1.4 baseline_mean=0.4 candidate_mean=0.56 bad_mean_ratio=1.4
- background_rms: baseline_median=25.0 candidate_median=35.0 bad_median_ratio=1.4 baseline_mean=25.0 candidate_mean=35.0 bad_mean_ratio=1.4
- snr: baseline_median=45.0 candidate_median=32.142857 bad_median_ratio=1.4 baseline_mean=45.0 candidate_mean=32.142857 bad_mean_ratio=1.4
- quality_score: baseline_median=800.0 candidate_median=571.428571 bad_median_ratio=1.4 baseline_mean=800.0 candidate_mean=571.428571 bad_mean_ratio=1.4
- weight: baseline_median=0.8 candidate_median=0.571429 bad_median_ratio=1.399999 baseline_mean=0.8 candidate_mean=0.571429 bad_mean_ratio=1.399999
